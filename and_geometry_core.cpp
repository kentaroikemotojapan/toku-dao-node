#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <vector>
#include <cmath>
#include <algorithm>
#include <string>
#include <cstring>
#include <stdexcept>
#include <thread>
#include <atomic>
#include <mutex>
#include <unordered_map>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <netdb.h>
#include <unistd.h>

namespace py = pybind11;

constexpr int DIM = 21;

#pragma pack(push, 1)
struct NodeStatePacket {
    char node_id[32];
    double state_vector[21];
    double free_energy;
    double phi_faith;
    double lambda_mirror;
};
#pragma pack(pop)

struct EvaluationResult {
    std::string status;
    std::string action;
    std::string reason;
    double updated_phi_faith;
    double free_energy;
    bool had_negative_eigenvalue;
    bool is_quarantined;
};

class GeometryCoreCPP {
private:
    double epsilon;
    double catastrophe_threshold;

    int rx_socket_fd = -1;
    std::atomic<bool> is_rx_running{false};
    std::thread rx_thread;
    std::mutex peer_mutex;
    std::unordered_map<std::string, double> peer_free_energy_map;
    std::vector<std::string> quarantined_peer_list;

    void jacobi_eigen(const std::vector<double>& A, std::vector<double>& eigenvalues, std::vector<double>& V) {
        std::vector<double> a = A;
        eigenvalues.assign(DIM, 0.0);
        V.assign(DIM * DIM, 0.0);
        for (int i = 0; i < DIM; ++i) { V[i * DIM + i] = 1.0; eigenvalues[i] = a[i * DIM + i]; }

        for (int iter = 0; iter < 100; ++iter) {
            double max_val = 0.0; int p = 0, q = 0;
            for (int i = 0; i < DIM - 1; ++i) {
                for (int j = i + 1; j < DIM; ++j) {
                    double val = std::abs(a[i * DIM + j]);
                    if (val > max_val) { max_val = val; p = i; q = j; }
                }
            }
            if (max_val < 1e-10) break;
            double app = a[p * DIM + p], aqq = a[q * DIM + q], apq = a[p * DIM + q];
            double phi = 0.5 * std::atan2(2.0 * apq, aqq - app);
            double c = std::cos(phi), s = std::sin(phi);
            a[p * DIM + p] = c * c * app - 2.0 * s * c * apq + s * s * aqq;
            a[q * DIM + q] = s * s * app + 2.0 * s * c * apq + c * c * aqq;
            a[p * DIM + q] = a[q * DIM + p] = 0.0;

            for (int i = 0; i < DIM; ++i) {
                if (i != p && i != q) {
                    double aip = a[i * DIM + p], aiq = a[i * DIM + q];
                    a[i * DIM + p] = a[p * DIM + i] = c * aip - s * aiq;
                    a[i * DIM + q] = a[q * DIM + i] = s * aip + c * aiq;
                }
                double vip = V[i * DIM + p], viq = V[i * DIM + q];
                V[i * DIM + p] = c * vip - s * viq;
                V[i * DIM + q] = s * vip + c * viq;
            }
        }
        for (int i = 0; i < DIM; ++i) eigenvalues[i] = a[i * DIM + i];
    }

    void rx_loop() {
        sockaddr_in src_addr;
        socklen_t addr_len = sizeof(src_addr);
        NodeStatePacket pkt;

        while (is_rx_running) {
            ssize_t bytes_read = recvfrom(rx_socket_fd, &pkt, sizeof(NodeStatePacket), 0,
                                          (struct sockaddr*)&src_addr, &addr_len);
            if (bytes_read == sizeof(NodeStatePacket)) {
                std::string sender_id(pkt.node_id);

                std::lock_guard<std::mutex> lock(peer_mutex);
                
                if (pkt.lambda_mirror < 0.01) {
                    if (std::find(quarantined_peer_list.begin(), quarantined_peer_list.end(), sender_id) == quarantined_peer_list.end()) {
                        quarantined_peer_list.push_back(sender_id);
                    }
                } else {
                    peer_free_energy_map[sender_id] = pkt.free_energy;
                }
            }
        }
    }

public:
    explicit GeometryCoreCPP(double eps = 1e-4, double threshold = 8.0) 
        : epsilon(eps), catastrophe_threshold(threshold) {}

    ~GeometryCoreCPP() {
        stop_p2p_listener();
    }

    void start_p2p_listener(int port = 9001) {
        if (is_rx_running) return;

        rx_socket_fd = socket(AF_INET, SOCK_DGRAM, 0);
        if (rx_socket_fd < 0) throw std::runtime_error("Failed to create UDP socket.");

        int reuse = 1;
        setsockopt(rx_socket_fd, SOL_SOCKET, SO_REUSEADDR, &reuse, sizeof(reuse));
#ifdef SO_REUSEPORT
        setsockopt(rx_socket_fd, SOL_SOCKET, SO_REUSEPORT, &reuse, sizeof(reuse));
#endif

        sockaddr_in local_addr{};
        local_addr.sin_family = AF_INET;
        local_addr.sin_port = htons(port);
        local_addr.sin_addr.s_addr = INADDR_ANY;

        if (bind(rx_socket_fd, (struct sockaddr*)&local_addr, sizeof(local_addr)) < 0) {
            close(rx_socket_fd);
            throw std::runtime_error("Failed to bind UDP socket.");
        }

        is_rx_running = true;
        rx_thread = std::thread(&GeometryCoreCPP::rx_loop, this);
    }

    void stop_p2p_listener() {
        if (is_rx_running) {
            is_rx_running = false;
            if (rx_socket_fd >= 0) {
                close(rx_socket_fd);
                rx_socket_fd = -1;
            }
            if (rx_thread.joinable()) rx_thread.join();
        }
    }

    std::unordered_map<std::string, double> get_active_peers() {
        std::lock_guard<std::mutex> lock(peer_mutex);
        return peer_free_energy_map;
    }

    std::vector<std::string> get_quarantined_peers() {
        std::lock_guard<std::mutex> lock(peer_mutex);
        return quarantined_peer_list;
    }

    std::vector<double> process_state_vector(
        const std::vector<double>& needs, 
        const std::vector<double>& arousal, 
        const std::vector<double>& phase) 
    {
        if (needs.size() != 9 || arousal.size() != 6 || phase.size() != 6) {
            throw std::invalid_argument("Needs(9), Arousal(6), Phase(6) dimensions mismatch.");
        }

        std::vector<double> raw_vec;
        raw_vec.reserve(DIM);
        raw_vec.insert(raw_vec.end(), needs.begin(), needs.end());
        raw_vec.insert(raw_vec.end(), arousal.begin(), arousal.end());
        raw_vec.insert(raw_vec.end(), phase.begin(), phase.end());

        double norm_sq = 0.0;
        double arousal_sum = 0.0;
        for (double v : raw_vec) norm_sq += v * v;
        for (double a : arousal) arousal_sum += a;

        double norm = std::sqrt(norm_sq);
        double arousal_mag = arousal_sum / 6.0;
        double scale = 1.0 + arousal_mag * 5.0;

        std::vector<double> state_vec(DIM);
        for (int i = 0; i < DIM; ++i) {
            state_vec[i] = (norm > 0.0 ? (raw_vec[i] / norm) : raw_vec[i]) * scale;
        }
        return state_vec;
    }

    EvaluationResult evaluate_and_dispatch(
        const std::string& node_id,
        const std::vector<double>& state_vector, 
        double lambda_mirror, 
        double current_phi_faith,
        py::buffer secret_cache_buf,
        const std::string& target_host = "127.0.0.1",
        int target_port = 9001) 
    {
        if (lambda_mirror < 0.01) {
            zeroize_buffer(secret_cache_buf);
            return {"PARASITIC_SEPSIS_DETECTED", "SLASH", 
                    "Dark Triad Topology Detected -> Self-Zeroization Triggered!", 
                    current_phi_faith, 0.0, false, true};
        }

        std::vector<double> hessian(DIM * DIM, 0.0);
        for (int i = 0; i < DIM; ++i) {
            for (int j = 0; j < DIM; ++j) {
                hessian[i * DIM + j] = state_vector[i] * state_vector[j];
                if (i == j) hessian[i * DIM + j] += 0.05;
            }
        }

        std::vector<double> eigenvalues(DIM), eigenvectors(DIM * DIM);
        jacobi_eigen(hessian, eigenvalues, eigenvectors);

        bool had_neg = false;
        std::vector<double> clipped_lambda(DIM);
        for (int i = 0; i < DIM; ++i) {
            if (eigenvalues[i] < 0.0) {
                had_neg = true;
                clipped_lambda[i] = std::max(std::abs(eigenvalues[i]), epsilon);
            } else {
                clipped_lambda[i] = eigenvalues[i];
            }
        }

        std::vector<double> g_munu(DIM * DIM, 0.0);
        for (int i = 0; i < DIM; ++i) {
            for (int j = 0; j < DIM; ++j) {
                double sum = 0.0;
                for (int k = 0; k < DIM; ++k) {
                    sum += eigenvectors[i * DIM + k] * clipped_lambda[k] * eigenvectors[j * DIM + k];
                }
                g_munu[i * DIM + j] = sum;
            }
        }

        double free_energy = 0.0;
        for (int i = 0; i < DIM; ++i) {
            double row_sum = 0.0;
            for (int j = 0; j < DIM; ++j) row_sum += g_munu[i * DIM + j] * state_vector[j];
            free_energy += state_vector[i] * row_sum;
        }
        free_energy *= 0.5;

        std::string status = "ISOTROPIC_EQUILIBRIUM";
        std::string action = "MINT";
        std::string reason = "Harmonic State in Metric Space";
        double updated_faith = current_phi_faith;

        if (free_energy > catastrophe_threshold) {
            double dissipated = free_energy - catastrophe_threshold;
            if (current_phi_faith >= dissipated) {
                status = "CATASTROPHE_BUFFERED";
                action = "MINT";
                reason = "Free Energy Spike Absorbed by Faith Anchor";
                updated_faith = current_phi_faith - dissipated;
            } else {
                status = "CATASTROPHE_SNAP_EXCEEDED";
                action = "SLASH";
                reason = "Unabsorbed Dissipative Energy Exceeded Threshold";
                updated_faith = 0.0;
            }
        }

        send_udp_packet(node_id, state_vector, free_energy, updated_faith, lambda_mirror, target_host, target_port);

        return {status, action, reason, updated_faith, free_energy, had_neg, false};
    }

    void send_raw_udp_packet(
        const std::string& node_id, 
        double free_energy, 
        double phi_faith, 
        double lambda_mirror, 
        const std::string& target_host = "127.0.0.1",
        int port = 9001) 
    {
        std::vector<double> dummy_vec(DIM, 0.1);
        send_udp_packet(node_id, dummy_vec, free_energy, phi_faith, lambda_mirror, target_host, port);
    }

    static void zeroize_buffer(py::buffer b) {
        py::buffer_info info = b.request();
        if (info.ptr && info.size > 0) {
            volatile char* p = static_cast<volatile char*>(info.ptr);
            size_t total_bytes = info.size * info.itemsize;
            for (size_t i = 0; i < total_bytes; ++i) p[i] = 0;
        }
    }

private:
    void send_udp_packet(const std::string& node_id, const std::vector<double>& state_vector,
                         double free_energy, double phi_faith, double lambda_mirror, 
                         const std::string& target_host, int port) 
    {
        int sock = socket(AF_INET, SOCK_DGRAM, 0);
        if (sock < 0) return;

        sockaddr_in addr{};
        addr.sin_family = AF_INET;
        addr.sin_port = htons(port);
        
        addr.sin_addr.s_addr = inet_addr(target_host.c_str());
        if (addr.sin_addr.s_addr == INADDR_NONE) {
            struct hostent* hp = gethostbyname(target_host.c_str());
            if (hp) {
                std::memcpy(&addr.sin_addr, hp->h_addr, hp->h_length);
            }
        }

        NodeStatePacket pkt{};
        std::strncpy(pkt.node_id, node_id.c_str(), 31);
        if (state_vector.size() == DIM) {
            std::memcpy(pkt.state_vector, state_vector.data(), DIM * sizeof(double));
        }
        pkt.free_energy = free_energy;
        pkt.phi_faith = phi_faith;
        pkt.lambda_mirror = lambda_mirror;

        sendto(sock, &pkt, sizeof(NodeStatePacket), 0, (struct sockaddr*)&addr, sizeof(addr));
        close(sock);
    }
};

PYBIND11_MODULE(and_geometry_cpp, m) {
    m.doc() = "AND Protocol C++ High-Performance Information Geometry Core";

    py::class_<EvaluationResult>(m, "EvaluationResult")
        .def_readonly("status", &EvaluationResult::status)
        .def_readonly("action", &EvaluationResult::action)
        .def_readonly("reason", &EvaluationResult::reason)
        .def_readonly("updated_phi_faith", &EvaluationResult::updated_phi_faith)
        .def_readonly("free_energy", &EvaluationResult::free_energy)
        .def_readonly("had_negative_eigenvalue", &EvaluationResult::had_negative_eigenvalue)
        .def_readonly("is_quarantined", &EvaluationResult::is_quarantined);

    py::class_<GeometryCoreCPP>(m, "GeometryCoreCPP")
        .def(py::init<double, double>(), py::arg("eps") = 1e-4, py::arg("threshold") = 8.0)
        .def("start_p2p_listener", &GeometryCoreCPP::start_p2p_listener, py::arg("port") = 9001)
        .def("stop_p2p_listener", &GeometryCoreCPP::stop_p2p_listener)
        .def("get_active_peers", &GeometryCoreCPP::get_active_peers)
        .def("get_quarantined_peers", &GeometryCoreCPP::get_quarantined_peers)
        .def("process_state_vector", &GeometryCoreCPP::process_state_vector)
        .def("evaluate_and_dispatch", &GeometryCoreCPP::evaluate_and_dispatch,
             py::arg("node_id"), py::arg("state_vector"), py::arg("lambda_mirror"),
             py::arg("current_phi_faith"), py::arg("secret_cache_buf"), 
             py::arg("target_host") = "127.0.0.1", py::arg("target_port") = 9001)
        .def("send_raw_udp_packet", &GeometryCoreCPP::send_raw_udp_packet,
             py::arg("node_id"), py::arg("free_energy"), py::arg("phi_faith"),
             py::arg("lambda_mirror"), py::arg("target_host") = "127.0.0.1", py::arg("port") = 9001)
        .def_static("zeroize_buffer", &GeometryCoreCPP::zeroize_buffer);
}