#include "pos_core.hpp"

extern "C" {
    POSCore* pos_crear(const char* db_path) {
        return new POSCore(db_path);
    }

    void pos_destruir(POSCore* pos) {
        delete pos;
    }

    bool pos_inicializar(POSCore* pos) {
        return pos->inicializarBD();
    }

    double pos_obtener_total_hoy(POSCore* pos) {
        return pos->obtenerResumenHoy().total_ventas;
    }
}