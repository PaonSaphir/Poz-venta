import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "verduleria_local.db")

class DatabaseManager:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS inventario (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT UNIQUE NOT NULL,
                    unidad TEXT NOT NULL,
                    costo REAL NOT NULL,
                    precio REAL NOT NULL,
                    stock_inicial REAL NOT NULL,
                    stock_actual REAL NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS historial (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticket_id TEXT NOT NULL,
                    fecha_hora TEXT NOT NULL,
                    producto TEXT NOT NULL,
                    cantidad REAL NOT NULL,
                    subtotal REAL NOT NULL,
                    medio_pago TEXT NOT NULL
                )
            """)
            conn.commit()

            cursor.execute("SELECT COUNT(*) FROM inventario")
            if cursor.fetchone()[0] == 0:
                productos_base = [
                    ("Tomate Larga Vida", "Kg", 800, 1500, 50, 4),
                    ("Palta Hass", "Kg", 3000, 4500, 20, 20),
                    ("Limón Malla", "Unidad", 500, 1000, 40, 3),
                    ("Aceite Vegetal 1L", "Unidad", 1800, 2500, 20, 20),
                    ("Arroz Grado 1", "Unidad", 900, 1400, 30, 30),
                    ("Bebida 1.5L", "Unidad", 1100, 1700, 25, 25)
                ]
                cursor.executemany("""
                    INSERT INTO inventario (nombre, unidad, costo, precio, stock_inicial, stock_actual)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, productos_base)
                conn.commit()

    def obtener_productos(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, nombre, unidad, costo, precio, stock_inicial, stock_actual FROM inventario")
            return cursor.fetchall()

    def obtener_nombres_productos(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT nombre FROM inventario")
            return [row[0] for row in cursor.fetchall()]

    def obtener_info_producto(self, nombre):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT precio, unidad FROM inventario WHERE nombre = ?", (nombre,))
            return cursor.fetchone()

    def actualizar_producto(self, p_id, nom, uni, cos, pre, stk):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE inventario SET nombre = ?, unidad = ?, costo = ?, precio = ?, stock_actual = ? WHERE id = ?
            """, (nom, uni, cos, pre, stk, p_id))
            conn.commit()

    def guardar_nuevo_producto(self, nom, uni, cos, pre, stk):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO inventario (nombre, unidad, costo, precio, stock_inicial, stock_actual)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (nom, uni, cos, pre, stk, stk))
            conn.commit()

    def eliminar_producto(self, p_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM inventario WHERE id = ?", (p_id,))
            conn.commit()

    def registrar_venta(self, ticket_id, fecha_hora, items, medio_pago_detalle):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            for item in items:
                cursor.execute("""
                    INSERT INTO historial (ticket_id, fecha_hora, producto, cantidad, subtotal, medio_pago)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (ticket_id, fecha_hora, item["nombre"], item["cant"], item["subtotal"], medio_pago_detalle))

                cursor.execute("""
                    UPDATE inventario SET stock_actual = stock_actual - ? WHERE nombre = ?
                """, (item["cant"], item["nombre"]))
            conn.commit()

    def obtener_historial(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT ticket_id, fecha_hora, producto, cantidad, subtotal, medio_pago FROM historial ORDER BY id DESC")
            return cursor.fetchall()

    def limpiar_historial(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM historial")
            conn.commit()

    def obtener_resumen_dia(self, fecha_str):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT SUM(subtotal),
                       SUM(CASE WHEN medio_pago = 'Efectivo' THEN subtotal ELSE 0 END),
                       SUM(CASE WHEN medio_pago != 'Efectivo' THEN subtotal ELSE 0 END)
                FROM historial
                WHERE fecha_hora LIKE ?
            """, (f"{fecha_str}%",))
            res = cursor.fetchone()
            return res[0] or 0.0, res[1] or 0.0, res[2] or 0.0

    def obtener_resumen_productos_dia(self, fecha_str):
        """Retorna una lista consolidada de los productos vendidos en una fecha específica: [(nombre, unidad, cantidad_total, total_dinero), ...]"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT producto, 
                       (SELECT unidad FROM inventario WHERE nombre = historial.producto) as unidad,
                       SUM(cantidad), 
                       SUM(subtotal)
                FROM historial
                WHERE fecha_hora LIKE ?
                GROUP BY producto
                ORDER BY SUM(subtotal) DESC
            """, (f"{fecha_str}%",))
            return cursor.fetchall()