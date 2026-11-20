#include "pos_core.hpp"
#include <sqlite3.h>
#include <iostream>
#include <ctime>

POSCore::POSCore(const std::string& db_path) : db_path_(db_path) {}
POSCore::~POSCore() {}

bool POSCore::inicializarBD() {
    sqlite3* db;
    if (sqlite3_open(db_path_.c_str(), &db) != SQLITE_OK) return false;

    const char* sql_inventario = 
        "CREATE TABLE IF NOT EXISTS inventario ("
        "id TEXT PRIMARY KEY, "
        "nombre TEXT NOT NULL, "
        "unidad_medida TEXT NOT NULL, "
        "costo REAL NOT NULL, "
        "precio_venta REAL NOT NULL, "
        "stock_inicial REAL NOT NULL);" ;

    const char* sql_historial = 
        "CREATE TABLE IF NOT EXISTS historial_ventas ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "ticket_id TEXT NOT NULL, "
        "fecha_hora DATETIME DEFAULT CURRENT_TIMESTAMP, "
        "producto_id TEXT NOT NULL, "
        "cantidad REAL NOT NULL, "
        "total REAL NOT NULL, "
        "medio_pago TEXT NOT NULL);" ;

    sqlite3_exec(db, sql_inventario, nullptr, nullptr, nullptr);
    sqlite3_exec(db, sql_historial, nullptr, nullptr, nullptr);
    sqlite3_close(db);
    return true;
}

bool POSCore::registrarVenta(const std::string& ticket_id, const std::string& medio_pago, const std::vector<ItemVenta>& items) {
    sqlite3* db;
    if (sqlite3_open(db_path_.c_str(), &db) != SQLITE_OK) return false;

    sqlite3_exec(db, "BEGIN TRANSACTION;", nullptr, nullptr, nullptr);

    const char* sql_insert = "INSERT INTO historial_ventas (ticket_id, producto_id, cantidad, total, medio_pago) VALUES (?, ?, ?, ?, ?);";
    sqlite3_stmt* stmt;

    for (const auto& item : items) {
        sqlite3_prepare_v2(db, sql_insert, -1, &stmt, nullptr);
        sqlite3_bind_text(stmt, 1, ticket_id.c_str(), -1, SQLITE_STATIC);
        sqlite3_bind_text(stmt, 2, item.producto_id.c_str(), -1, SQLITE_STATIC);
        sqlite3_bind_double(stmt, 3, item.cantidad_o_peso);
        sqlite3_bind_double(stmt, 4, item.subtotal);
        sqlite3_bind_text(stmt, 5, medio_pago.c_str(), -1, SQLITE_STATIC);

        sqlite3_step(stmt);
        sqlite3_finalize(stmt);
    }

    sqlite3_exec(db, "COMMIT;", nullptr, nullptr, nullptr);
    sqlite3_close(db);
    return true;
}

ResumenDiario POSCore::obtenerResumenHoy() {
    ResumenDiario res = {0.0, 0.0, 0.0, 0.0};
    sqlite3* db;
    if (sqlite3_open(db_path_.c_str(), &db) != SQLITE_OK) return res;

    // Sumar ventas correspondientes únicamente a la fecha actual (DATE('now', 'localtime'))
    const char* sql = 
        "SELECT "
        "COALESCE(SUM(total), 0), "
        "COALESCE(SUM(CASE WHEN medio_pago = 'Efectivo' THEN total ELSE 0 END), 0), "
        "COALESCE(SUM(CASE WHEN medio_pago != 'Efectivo' THEN total ELSE 0 END), 0) "
        "FROM historial_ventas WHERE DATE(fecha_hora, 'localtime') = DATE('now', 'localtime');";

    sqlite3_stmt* stmt;
    if (sqlite3_prepare_v2(db, sql, -1, &stmt, nullptr) == SQLITE_OK) {
        if (sqlite3_step(stmt) == SQLITE_ROW) {
            res.total_ventas = sqlite3_column_double(stmt, 0);
            res.total_efectivo = sqlite3_column_double(stmt, 1);
            res.total_tarjeta = sqlite3_column_double(stmt, 2);
        }
    }
    sqlite3_finalize(stmt);
    sqlite3_close(db);
    return res;
}