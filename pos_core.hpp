#pragma once
#include <string>
#include <vector>

struct Producto {
    std::string id;
    std::string nombre;
    std::string unidad_medida; // "Kg" o "Unidad"
    double costo;
    double precio_venta;
    double stock_inicial;
    double stock_vendido;
    double stock_actual;
};

struct ItemVenta {
    std::string producto_id;
    double cantidad_o_peso;
    double subtotal;
};

struct ResumenDiario {
    double total_ventas;
    double total_efectivo;
    double total_tarjeta;
    double ganancia_estimada;
};

class POSCore {
public:
    POSCore(const std::string& db_path);
    ~POSCore();

    // Inicializar tablas en SQLite local
    bool inicializarBD();

    // Productos / Inventario
    bool agregarProducto(const Producto& p);
    std::vector<Producto> obtenerInventario();
    Producto obtenerProductoPorID(const std::string& id);

    // Procesar Venta (Equivalente al botón 'CONFIRMAR VENTA')
    bool registrarVenta(const std::string& ticket_id, 
                        const std::string& medio_pago, 
                        const std::vector<ItemVenta>& items);

    // Métricas del día actual
    ResumenDiario obtenerResumenHoy();

private:
    std::string db_path_;
};