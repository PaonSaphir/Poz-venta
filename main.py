import customtkinter as ctk
import os
from datetime import datetime
from tkinter import messagebox
from database import DatabaseManager

# Configuración visual global
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("green")

# Instanciar el gestor de base de datos
db = DatabaseManager()


class POSApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Punto de Venta - Verdulería & Minimarket")
        self.geometry("1200x720")
        self.minsize(980, 620)

        self.ticket_items = []
        self.entry_enfocado = None
        self.limpiar_al_escribir = True
        self.num_ticket_actual = 1

        self._crear_interfaz_principal()
        self._vincular_atajos_teclado()

    def _crear_interfaz_principal(self):
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # BARRA DE NAVEGACIÓN
        frame_nav = ctk.CTkFrame(self, height=50, corner_radius=0, fg_color="#1F2937")
        frame_nav.grid(row=0, column=0, sticky="ew")

        btn_vistas = [
            ("🛒 TERMINAL", self._mostrar_terminal),
            ("📦 INVENTARIO", self._mostrar_inventario),
            ("🏷️ LETREROS", self._mostrar_letreros),
            ("📜 HISTORIAL", self._mostrar_historial),
            ("📊 RESUMEN DIARIO", self._mostrar_resumen)
        ]

        for texto, comando in btn_vistas:
            btn = ctk.CTkButton(
                frame_nav, text=texto, font=("Roboto", 13, "bold"),
                fg_color="transparent", hover_color="#374151",
                height=40, command=comando
            )
            btn.pack(side="left", padx=8, pady=5)

        # CONTENEDOR VISTAS
        self.container = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.container.grid(row=1, column=0, sticky="nsew")
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.view_terminal = ctk.CTkFrame(self.container, fg_color="transparent")
        self.view_inventario = ctk.CTkFrame(self.container, fg_color="transparent")
        self.view_letreros = ctk.CTkFrame(self.container, fg_color="transparent")
        self.view_historial = ctk.CTkFrame(self.container, fg_color="transparent")
        self.view_resumen = ctk.CTkFrame(self.container, fg_color="transparent")

        self._construir_vista_terminal()
        self._construir_vista_inventario()
        self._construir_vista_letreros()
        self._construir_vista_historial()
        self._construir_vista_resumen()

        self._mostrar_terminal()

    def _vincular_atajos_teclado(self):
        self.bind("<Return>", lambda event: self._agregar_item_desde_teclado())
        self.bind("<F12>", lambda event: self._confirmar_venta())

    def _agregar_item_desde_teclado(self):
        if str(self.view_terminal.winfo_ismapped()) == '1':
            self._agregar_item()

    # ---------------------------------------------------------
    # 1. VISTA TERMINAL DE VENTA
    # ---------------------------------------------------------
    def _construir_vista_terminal(self):
        self.view_terminal.grid_columnconfigure(0, weight=6)
        self.view_terminal.grid_columnconfigure(1, weight=4)
        self.view_terminal.grid_rowconfigure(0, weight=1)

        frame_ticket = ctk.CTkFrame(self.view_terminal, corner_radius=10)
        frame_ticket.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        frame_ticket.grid_rowconfigure(1, weight=1)
        frame_ticket.grid_columnconfigure(0, weight=1)

        lbl_titulo = ctk.CTkLabel(frame_ticket, text="🛒 TICKET DE VENTA (Enter: Agregar | F12: Cobrar)", font=("Roboto", 16, "bold"))
        lbl_titulo.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.scroll_ticket = ctk.CTkScrollableFrame(frame_ticket, fg_color="#1E1E1E")
        self.scroll_ticket.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")

        frame_pago_resumen = ctk.CTkFrame(frame_ticket, fg_color="#111827", corner_radius=8)
        frame_pago_resumen.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        frame_pago_resumen.grid_columnconfigure((0,1,2), weight=1)

        self.lbl_total = ctk.CTkLabel(frame_pago_resumen, text="TOTAL: $0", font=("Roboto", 22, "bold"), text_color="#10B981")
        self.lbl_total.grid(row=0, column=0, padx=10, pady=10)

        self.lbl_paga_con = ctk.CTkLabel(frame_pago_resumen, text="PAGA CON: $0", font=("Roboto", 18, "bold"), text_color="#F59E0B")
        self.lbl_paga_con.grid(row=0, column=1, padx=10, pady=10)

        self.lbl_vuelto = ctk.CTkLabel(frame_pago_resumen, text="VUELTO: $0", font=("Roboto", 22, "bold"), text_color="#3B82F6")
        self.lbl_vuelto.grid(row=0, column=2, padx=10, pady=10)

        frame_control = ctk.CTkFrame(self.view_terminal, corner_radius=10)
        frame_control.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        frame_control.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(frame_control, text="Producto:", font=("Roboto", 13, "bold")).grid(row=0, column=0, columnspan=2, padx=10, pady=(8,0), sticky="w")
        self.cmb_producto = ctk.CTkOptionMenu(frame_control, values=[], font=("Roboto", 13), height=35)
        self.cmb_producto.grid(row=1, column=0, columnspan=2, padx=10, pady=3, sticky="ew")
        self._actualizar_combo_productos()

        ctk.CTkLabel(frame_control, text="Medio de Pago:", font=("Roboto", 12, "bold")).grid(row=2, column=0, padx=10, pady=(6,0), sticky="w")
        self.lbl_pago_dinamico = ctk.CTkLabel(frame_control, text="Paga Con ($):", font=("Roboto", 12, "bold"))
        self.lbl_pago_dinamico.grid(row=2, column=1, padx=10, pady=(6,0), sticky="w")

        self.cmb_pago = ctk.CTkOptionMenu(
            frame_control, values=["Efectivo", "Débito", "Crédito", "Transferencia"],
            font=("Roboto", 13, "bold"), height=38, fg_color="#D97706", button_color="#B45309", button_hover_color="#92400E",
            command=self._al_cambiar_medio_pago
        )
        self.cmb_pago.grid(row=3, column=0, padx=(10,4), pady=3, sticky="ew")

        self.ent_pago_val = ctk.CTkEntry(frame_control, font=("Roboto", 18, "bold"), justify="center", height=38)
        self.ent_pago_val.grid(row=3, column=1, padx=(4,10), pady=3, sticky="ew")
        self.ent_pago_val.bind("<FocusIn>", lambda e: self._seleccionar_entry(self.ent_pago_val))

        ctk.CTkLabel(frame_control, text="Cantidad / Peso (Kg o Ud):", font=("Roboto", 13, "bold")).grid(row=4, column=0, columnspan=2, padx=10, pady=(8,0), sticky="w")
        self.ent_cantidad = ctk.CTkEntry(frame_control, font=("Roboto", 20, "bold"), justify="center", height=40)
        self.ent_cantidad.grid(row=5, column=0, columnspan=2, padx=10, pady=3, sticky="ew")
        self.ent_cantidad.insert(0, "1")
        self.ent_cantidad.bind("<FocusIn>", lambda e: self._seleccionar_entry(self.ent_cantidad))

        self.entry_enfocado = self.ent_cantidad

        frame_pad = ctk.CTkFrame(frame_control, fg_color="transparent")
        frame_pad.grid(row=6, column=0, columnspan=2, padx=10, pady=5, sticky="nsew")
        frame_pad.grid_columnconfigure((0,1,2), weight=1)

        botones_pad = [
            ('7', 0, 0), ('8', 0, 1), ('9', 0, 2),
            ('4', 1, 0), ('5', 1, 1), ('6', 1, 2),
            ('1', 2, 0), ('2', 2, 1), ('3', 2, 2),
            ('0', 3, 0), ('.', 3, 1), ('⌫', 3, 2)
        ]

        for (texto, fila, col) in botones_pad:
            btn = ctk.CTkButton(
                frame_pad, text=texto, font=("Roboto", 18, "bold"),
                height=40, fg_color="#374151", hover_color="#4B5563",
                command=lambda t=texto: self._presionar_tecla(t)
            )
            btn.grid(row=fila, column=col, padx=2, pady=2, sticky="nsew")

        btn_agregar = ctk.CTkButton(
            frame_control, text="➕ AGREGAR ITEM [Enter]", font=("Roboto", 15, "bold"),
            height=40, fg_color="#2563EB", hover_color="#1D4ED8", command=self._agregar_item
        )
        btn_agregar.grid(row=7, column=0, columnspan=2, padx=10, pady=6, sticky="ew")

        btn_cobrar = ctk.CTkButton(
            frame_control, text="✔ CONFIRMAR VENTA [F12]", font=("Roboto", 18, "bold"),
            height=48, fg_color="#059669", hover_color="#047857", command=self._confirmar_venta
        )
        btn_cobrar.grid(row=8, column=0, columnspan=2, padx=10, pady=(4,10), sticky="ew")

    def _seleccionar_entry(self, entry_widget):
        self.entry_enfocado = entry_widget
        self.limpiar_al_escribir = True

    def _al_cambiar_medio_pago(self, opcion):
        self.ent_pago_val.delete(0, ctk.END)
        self.limpiar_al_escribir = True

        if opcion == "Efectivo":
            self.lbl_pago_dinamico.configure(text="Paga Con ($):")
            self.ent_pago_val.configure(state="normal")
            self.lbl_paga_con.configure(text="PAGA CON: $0")
            self.lbl_vuelto.configure(text="VUELTO: $0")

        elif opcion == "Crédito":
            self.lbl_pago_dinamico.configure(text="Cuotas:")
            self.ent_pago_val.configure(state="normal")
            self.ent_pago_val.insert(0, "1")
            self.lbl_paga_con.configure(text="CUOTAS: 1")
            self._recalcular_pago_dinamico()

        elif opcion in ["Débito", "Transferencia"]:
            self.lbl_pago_dinamico.configure(text="Monto Exacto:")
            self.ent_pago_val.configure(state="disabled")
            total = sum(i["subtotal"] for i in self.ticket_items)
            self.lbl_paga_con.configure(text=f"MONTO: ${total:,.0f}")
            self.lbl_vuelto.configure(text="VUELTO: $0")

    def _recalcular_pago_dinamico(self):
        opcion = self.cmb_pago.get()
        total = sum(i["subtotal"] for i in self.ticket_items)

        if opcion == "Efectivo":
            try:
                paga_con = float(self.ent_pago_val.get()) if self.ent_pago_val.get() else 0.0
            except ValueError:
                paga_con = 0.0
            vuelto = max(0.0, paga_con - total)
            self.lbl_paga_con.configure(text=f"PAGA CON: ${paga_con:,.0f}")
            self.lbl_vuelto.configure(text=f"VUELTO: ${vuelto:,.0f}")

        elif opcion == "Crédito":
            try:
                cuotas = int(float(self.ent_pago_val.get())) if self.ent_pago_val.get() else 1
                cuotas = max(1, cuotas)
            except ValueError:
                cuotas = 1

            monto_cuota = total / cuotas if total > 0 else 0
            self.lbl_paga_con.configure(text=f"CUOTAS: {cuotas}")
            self.lbl_vuelto.configure(text=f"VALOR CUOTA: ${monto_cuota:,.0f}")

    def _actualizar_combo_productos(self):
        prods = db.obtener_nombres_productos()
        if prods:
            self.cmb_producto.configure(values=prods)
            self.cmb_producto.set(prods[0])

    def _presionar_tecla(self, tecla):
        if not self.entry_enfocado or self.entry_enfocado.cget("state") == "disabled":
            self.entry_enfocado = self.ent_cantidad

        val_actual = self.entry_enfocado.get()

        if tecla == '⌫':
            self.entry_enfocado.delete(len(val_actual)-1, ctk.END)
            if len(self.entry_enfocado.get()) == 0:
                self.limpiar_al_escribir = True
        else:
            if self.limpiar_al_escribir:
                self.entry_enfocado.delete(0, ctk.END)
                self.limpiar_al_escribir = False
            self.entry_enfocado.insert(ctk.END, tecla)

        if self.entry_enfocado == self.ent_pago_val:
            self._recalcular_pago_dinamico()

    def _agregar_item(self):
        prod_nombre = self.cmb_producto.get()
        try:
            cant = float(self.ent_cantidad.get())
        except ValueError:
            cant = 1.0

        row = db.obtener_info_producto(prod_nombre)
        if not row:
            return
        precio, unidad = row

        subtotal = cant * precio
        self.ticket_items.append({
            "nombre": prod_nombre,
            "cant": cant,
            "unidad": unidad,
            "subtotal": subtotal
        })

        self._renderizar_ticket()
        self.ent_cantidad.delete(0, ctk.END)
        self.ent_cantidad.insert(0, "1")
        self._seleccionar_entry(self.ent_cantidad)

    def _eliminar_item_por_indice(self, idx):
        if 0 <= idx < len(self.ticket_items):
            self.ticket_items.pop(idx)
            self._renderizar_ticket()

    def _renderizar_ticket(self):
        for widget in self.scroll_ticket.winfo_children():
            widget.destroy()

        total = 0
        for idx, item in enumerate(self.ticket_items):
            item_frame = ctk.CTkFrame(self.scroll_ticket, fg_color="#2D3748", height=38)
            item_frame.pack(fill="x", padx=2, pady=3, expand=True)

            txt = f"{item['nombre'][:16]:<16} x{item['cant']} {item['unidad']}  |  ${item['subtotal']:,.0f}"
            lbl = ctk.CTkLabel(item_frame, text=txt, font=("Consolas", 14, "bold"), anchor="w")
            lbl.pack(side="left", padx=10, fill="x", expand=True)

            btn_x = ctk.CTkButton(
                item_frame, text="❌", width=30, height=28,
                fg_color="#DC2626", hover_color="#991B1B",
                command=lambda i=idx: self._eliminar_item_por_indice(i)
            )
            btn_x.pack(side="right", padx=5)

            total += item["subtotal"]

        self.lbl_total.configure(text=f"TOTAL: ${total:,.0f}")
        self._recalcular_pago_dinamico()

    def _confirmar_venta(self):
        if not self.ticket_items:
            return

        ticket_id = f"T-{self.num_ticket_actual:04d}"
        fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        medio_pago = self.cmb_pago.get()

        if medio_pago == "Crédito":
            try:
                cuotas = int(float(self.ent_pago_val.get())) if self.ent_pago_val.get() else 1
            except ValueError:
                cuotas = 1
            pago_detalle = f"Crédito ({cuotas} cuota{'s' if cuotas > 1 else ''})"
        else:
            pago_detalle = medio_pago

        db.registrar_venta(ticket_id, fecha_hora, self.ticket_items, pago_detalle)

        self.num_ticket_actual += 1
        self.ticket_items.clear()
        self._renderizar_ticket()
        self.ent_pago_val.delete(0, ctk.END)
        self._al_cambiar_medio_pago(medio_pago)

        self._construir_vista_inventario()
        self._construir_vista_historial()
        self._construir_vista_resumen()

    # ---------------------------------------------------------
    # 2. VISTA INVENTARIO
    # ---------------------------------------------------------
    def _construir_vista_inventario(self):
        for w in self.view_inventario.winfo_children():
            w.destroy()

        ctk.CTkLabel(self.view_inventario, text="📦 GESTIÓN DE INVENTARIO (🔴 Stock Crítico ≤ 5)", font=("Roboto", 22, "bold")).pack(padx=20, pady=10)

        frame_form = ctk.CTkFrame(self.view_inventario)
        frame_form.pack(fill="x", padx=20, pady=5)

        self.ent_inv_nombre = ctk.CTkEntry(frame_form, placeholder_text="Nombre", width=160)
        self.ent_inv_nombre.pack(side="left", padx=4, pady=8)

        self.cmb_inv_unidad = ctk.CTkOptionMenu(frame_form, values=["Kg", "Unidad"], width=85)
        self.cmb_inv_unidad.pack(side="left", padx=4)

        self.ent_inv_costo = ctk.CTkEntry(frame_form, placeholder_text="Costo $", width=85)
        self.ent_inv_costo.pack(side="left", padx=4)

        self.ent_inv_precio = ctk.CTkEntry(frame_form, placeholder_text="Precio $", width=95)
        self.ent_inv_precio.pack(side="left", padx=4)

        self.ent_inv_stock = ctk.CTkEntry(frame_form, placeholder_text="Stock", width=85)
        self.ent_inv_stock.pack(side="left", padx=4)

        btn_guardar = ctk.CTkButton(frame_form, text="➕ CREAR", fg_color="#059669", width=90, command=self._guardar_nuevo_producto)
        btn_guardar.pack(side="left", padx=8)

        scroll_inv = ctk.CTkScrollableFrame(self.view_inventario, fg_color="#1E1E1E")
        scroll_inv.pack(fill="both", expand=True, padx=20, pady=10)

        rows = db.obtener_productos()

        for r in rows:
            p_id, nom, uni, cos, pre, st_init, st_act = r
            color_fila = "#7F1D1D" if st_act <= 5 else "#2D3748"

            f = ctk.CTkFrame(scroll_inv, fg_color=color_fila)
            f.pack(fill="x", padx=5, pady=3)

            e_nom = ctk.CTkEntry(f, width=150)
            e_nom.insert(0, nom)
            e_nom.pack(side="left", padx=4, pady=5)

            c_uni = ctk.CTkOptionMenu(f, values=["Kg", "Unidad"], width=80)
            c_uni.set(uni)
            c_uni.pack(side="left", padx=4)

            e_cos = ctk.CTkEntry(f, width=75)
            e_cos.insert(0, str(cos))
            e_cos.pack(side="left", padx=4)

            e_pre = ctk.CTkEntry(f, width=85)
            e_pre.insert(0, str(pre))
            e_pre.pack(side="left", padx=4)

            e_stk = ctk.CTkEntry(f, width=75)
            e_stk.insert(0, str(st_act))
            e_stk.pack(side="left", padx=4)

            btn_upd = ctk.CTkButton(
                f, text="💾 GUARDAR", width=85, fg_color="#3B82F6", hover_color="#2563EB",
                command=lambda id_p=p_id, en=e_nom, cu=c_uni, ec=e_cos, ep=e_pre, es=e_stk:
                    self._actualizar_producto_fila(id_p, en.get(), cu.get(), ec.get(), ep.get(), es.get())
            )
            btn_upd.pack(side="right", padx=4)

            btn_del = ctk.CTkButton(f, text="🗑️", width=35, fg_color="#DC2626", command=lambda id_p=p_id: self._eliminar_producto(id_p))
            btn_del.pack(side="right", padx=4)

    def _actualizar_producto_fila(self, p_id, nom, uni, cos, pre, stk):
        try:
            c = float(cos)
            p = float(pre)
            s = float(stk)
        except ValueError:
            return

        db.actualizar_producto(p_id, nom, uni, c, p, s)
        self._construir_vista_inventario()
        self._actualizar_combo_productos()

    def _guardar_nuevo_producto(self):
        nom = self.ent_inv_nombre.get()
        uni = self.cmb_inv_unidad.get()
        try:
            cos = float(self.ent_inv_costo.get())
            pre = float(self.ent_inv_precio.get())
            stk = float(self.ent_inv_stock.get())
        except ValueError:
            return

        if nom:
            db.guardar_nuevo_producto(nom, uni, cos, pre, stk)
            self._construir_vista_inventario()
            self._actualizar_combo_productos()

    def _eliminar_producto(self, p_id):
        db.eliminar_producto(p_id)
        self._construir_vista_inventario()
        self._actualizar_combo_productos()

    # ---------------------------------------------------------
    # 3. VISTA LETREROS
    # ---------------------------------------------------------
    def _construir_vista_letreros(self):
        for w in self.view_letreros.winfo_children():
            w.destroy()

        ctk.CTkLabel(self.view_letreros, text="🏷️ GENERADOR DE LETREROS DE PRECIOS", font=("Roboto", 22, "bold")).pack(padx=20, pady=10)

        frame_sel = ctk.CTkFrame(self.view_letreros)
        frame_sel.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(frame_sel, text="Seleccione Producto:", font=("Roboto", 14, "bold")).pack(side="left", padx=10)
        
        self.cmb_letrero_prod = ctk.CTkOptionMenu(frame_sel, values=[], font=("Roboto", 14), width=220, command=self._actualizar_vista_letrero)
        self.cmb_letrero_prod.pack(side="left", padx=10)

        prods = db.obtener_nombres_productos()
        if prods:
            self.cmb_letrero_prod.configure(values=prods)
            self.cmb_letrero_prod.set(prods[0])

        btn_imp = ctk.CTkButton(frame_sel, text="🖨️ EXPORTAR / GUARDAR LETRERO (PNG)", fg_color="#D97706", hover_color="#B45309", command=self._exportar_letrero_png)
        btn_imp.pack(side="right", padx=10)

        self.frame_cartel = ctk.CTkFrame(self.view_letreros, fg_color="white", width=480, height=320, corner_radius=15)
        self.frame_cartel.pack(padx=20, pady=20)
        self.frame_cartel.pack_propagate(False)

        self.lbl_cartel_nom = ctk.CTkLabel(self.frame_cartel, text="", font=("Arial", 28, "bold"), text_color="black")
        self.lbl_cartel_nom.pack(pady=(40, 10))

        self.lbl_cartel_precio = ctk.CTkLabel(self.frame_cartel, text="", font=("Arial", 54, "bold"), text_color="#DC2626")
        self.lbl_cartel_precio.pack(pady=10)

        self.lbl_cartel_uni = ctk.CTkLabel(self.frame_cartel, text="", font=("Arial", 20, "bold"), text_color="#4B5563")
        self.lbl_cartel_uni.pack(pady=5)

        self._actualizar_vista_letrero(None)

    def _actualizar_vista_letrero(self, choice):
        prod_sel = self.cmb_letrero_prod.get()
        if not prod_sel:
            return

        row = db.obtener_info_producto(prod_sel)
        if row:
            precio, unidad = row
            self.lbl_cartel_nom.configure(text=prod_sel)
            self.lbl_cartel_precio.configure(text=f"${precio:,.0f}")
            self.lbl_cartel_uni.configure(text=f"por {unidad}")

    def _exportar_letrero_png(self):
        from tkinter import filedialog
        from PIL import Image, ImageDraw, ImageFont

        prod_sel = self.cmb_letrero_prod.get()
        if not prod_sel:
            return

        row = db.obtener_info_producto(prod_sel)
        if not row:
            return
        precio, unidad = row

        reporte_path = filedialog.asksaveasfilename(
            title="Guardar Letrero de Precio",
            defaultextension=".png",
            filetypes=[("Imagen PNG para Impresión (*.png)", "*.png")],
            initialfile=f"Letrero_{prod_sel.replace(' ', '_')}.png"
        )

        if not reporte_path:
            return

        img_width, img_height = 1200, 800
        image = Image.new("RGB", (img_width, img_height), "white")
        draw = ImageDraw.Draw(image)

        draw.rectangle([25, 25, img_width - 25, img_height - 25], outline="black", width=14)

        try:
            font_nombre = ImageFont.truetype("arial.ttf", 68)
            font_precio = ImageFont.truetype("arial.ttf", 160)
            font_unidad = ImageFont.truetype("arial.ttf", 50)
        except IOError:
            font_nombre = ImageFont.load_default()
            font_precio = ImageFont.load_default()
            font_unidad = ImageFont.load_default()

        texto_nombre = prod_sel.upper()
        texto_precio = f"${precio:,.0f}"
        texto_unidad = f"POR {unidad.upper()}"

        def dibujar_centrado(draw_obj, text, font, y_pos, fill_color):
            bbox = draw_obj.textbbox((0, 0), text, font=font)
            w = bbox[2] - bbox[0]
            x = (img_width - w) / 2
            draw_obj.text((x, y_pos), text, font=font, fill=fill_color)

        dibujar_centrado(draw, texto_nombre, font_nombre, 110, "black")
        dibujar_centrado(draw, texto_precio, font_precio, 260, "#DC2626")
        dibujar_centrado(draw, texto_unidad, font_unidad, 530, "#4B5563")

        image.save(reporte_path)
        os.system(f'start "" "{reporte_path}"' if os.name == 'nt' else f'xdg-open "{reporte_path}"')
        messagebox.showinfo("Éxito", f"Letrero generado como imagen PNG en:\n{reporte_path}")

    # ---------------------------------------------------------
    # 4. VISTA HISTORIAL
    # ---------------------------------------------------------
    def _construir_vista_historial(self):
        for w in self.view_historial.winfo_children():
            w.destroy()

        frame_top = ctk.CTkFrame(self.view_historial, fg_color="transparent")
        frame_top.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(frame_top, text="📜 HISTORIAL DE VENTAS", font=("Roboto", 22, "bold")).pack(side="left")

        btn_excel = ctk.CTkButton(
            frame_top, text="📄 EXPORTAR EXCEL", font=("Roboto", 13, "bold"),
            fg_color="#059669", hover_color="#047857", height=35, command=self._exportar_historial_excel
        )
        btn_excel.pack(side="right", padx=5)

        btn_limpiar = ctk.CTkButton(
            frame_top, text="🗑️ LIMPIAR", font=("Roboto", 13, "bold"),
            fg_color="#991B1B", hover_color="#7F1D1D", height=35, command=self._limpiar_historial_db
        )
        btn_limpiar.pack(side="right", padx=5)

        scroll_h = ctk.CTkScrollableFrame(self.view_historial, fg_color="#1E1E1E")
        scroll_h.pack(fill="both", expand=True, padx=20, pady=10)

        rows = db.obtener_historial()

        for r in rows:
            t_id, f_h, prod, cant, sub, pago = r
            f = ctk.CTkFrame(scroll_h, fg_color="#2D3748")
            f.pack(fill="x", padx=5, pady=3)
            txt = f"Ticket: {t_id:<7} | Fecha: {f_h} | {prod:<18} x{cant:<4} | Total: ${sub:<7} | Pago: {pago}"
            ctk.CTkLabel(f, text=txt, font=("Consolas", 13)).pack(side="left", padx=10, pady=5)

    def _exportar_historial_excel(self):
        import csv
        from tkinter import filedialog

        rows = db.obtener_historial()

        if not rows:
            messagebox.showinfo("Exportar Reporte", "El historial se encuentra vacío.")
            return

        reporte_path = filedialog.asksaveasfilename(
            title="Guardar Reporte para Excel",
            defaultextension=".csv",
            filetypes=[("Archivo de Excel (*.csv)", "*.csv"), ("Todos los archivos (*.*)", "*.*")],
            initialfile=f"Historial_Ventas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )

        if not reporte_path:
            return

        with open(reporte_path, mode="w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(["N° Ticket", "Fecha / Hora", "Producto", "Cantidad/Peso", "Total ($)", "Medio de Pago"])
            for r in rows:
                writer.writerow([r[0], r[1], r[2], r[3], r[4], r[5]])

        messagebox.showinfo("Guardado Exitoso", f"El reporte fue guardado correctamente para Excel en:\n{reporte_path}")

    def _limpiar_historial_db(self):
        if messagebox.askyesno("Limpiar Historial", "¿Desea borrar permanentemente todos los registros del historial?"):
            db.limpiar_historial()
            self._construir_vista_historial()
            self._construir_vista_resumen()

    def _exportar_resumen_pdf(self):
        from tkinter import filedialog
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors

        hoy = datetime.now().strftime("%Y-%m-%d")
        tot_ventas, tot_efectivo, tot_tarjeta = db.obtener_resumen_dia(hoy)
        productos_dia = db.obtener_resumen_productos_dia(hoy)

        if tot_ventas == 0:
            messagebox.showinfo("Exportar PDF", "No hay registros de ventas para el día de hoy.")
            return

        reporte_path = filedialog.asksaveasfilename(
            title="Guardar Resumen Diario en PDF",
            defaultextension=".pdf",
            filetypes=[("Archivo PDF (*.pdf)", "*.pdf")],
            initialfile=f"Arqueo_Diario_{hoy.replace('-', '')}.pdf"
        )

        if not reporte_path:
            return

        try:
            doc = SimpleDocTemplate(reporte_path, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
            story = []
            styles = getSampleStyleSheet()

            titulo_style = ParagraphStyle('TituloDoc', parent=styles['Heading1'], fontSize=20, textColor=colors.HexColor('#1F2937'), alignment=1, spaceAfter=15)
            sub_style = ParagraphStyle('SubTitulo', parent=styles['Heading2'], fontSize=14, textColor=colors.HexColor('#059669'), spaceAfter=10)
            normal_style = styles['Normal']

            # ==========================================
            # HOJA 1: RESUMEN FINANCIERO Y ARQUEO DE CAJA
            # ==========================================
            story.append(Paragraph("<b>ARQUEO Y RESUMEN DIARIO DE CAJA</b>", titulo_style))
            story.append(Paragraph(f"<b>Fecha de Emisión:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", normal_style))
            story.append(Spacer(1, 20))

            story.append(Paragraph("1. Desglose de Ingresos por Medio de Pago", sub_style))
            
            data_financiera = [
                ["Medio de Pago", "Monto Recaudado"],
                ["Efectivo en Caja", f"${tot_efectivo:,.0f}"],
                ["Débito / Transferencia / Tarjetas", f"${tot_tarjeta:,.0f}"],
                ["TOTAL GENERAL RECAUDADO", f"${tot_ventas:,.0f}"]
            ]

            t_fin = Table(data_financiera, colWidths=[250, 200])
            t_fin.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (1, 0), colors.HexColor('#1F2937')),
                ('TEXTCOLOR', (0, 0), (1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#10B981')),
                ('TEXTCOLOR', (0, -1), (-1, -1), colors.whitesmoke),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#D1D5DB')),
                ('PADDING', (0, 0), (-1, -1), 8),
            ]))
            story.append(t_fin)
            
            story.append(PageBreak())

            # ==========================================
            # HOJA 2: CONSOLIDADO DE PRODUCTOS VENDIDOS
            # ==========================================
            story.append(Paragraph(f"<b>CONSOLIDADO DE PRODUCTOS VENDIDOS ({hoy})</b>", titulo_style))
            story.append(Paragraph("Detalle de cantidades y volumen de venta por artículo:", normal_style))
            story.append(Spacer(1, 15))

            data_prods = [["Producto", "Unidad", "Cantidad Total Vendida", "Total Recaudado ($)"]]
            
            suma_verificacion = 0
            for prod, unidad, cant_tot, sub_tot in productos_dia:
                data_prods.append([str(prod), str(unidad), f"{cant_tot:g}", f"${sub_tot:,.0f}"])
                suma_verificacion += sub_tot

            data_prods.append(["CUADRATURA TOTAL", "", "", f"${suma_verificacion:,.0f}"])

            t_prod = Table(data_prods, colWidths=[180, 80, 120, 120])
            t_prod.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1F2937')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#3B82F6')),
                ('TEXTCOLOR', (0, -1), (-1, -1), colors.whitesmoke),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#D1D5DB')),
                ('PADDING', (0, 0), (-1, -1), 6),
            ]))
            story.append(t_prod)

            doc.build(story)
            os.system(f'start "" "{reporte_path}"' if os.name == 'nt' else f'xdg-open "{reporte_path}"')
            messagebox.showinfo("Éxito", f"Reporte PDF generado correctamente en:\n{reporte_path}")

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar el PDF:\n{str(e)}")

    # ---------------------------------------------------------
    # 5. VISTA RESUMEN DIARIO
    # ---------------------------------------------------------
    def _construir_vista_resumen(self):
        for w in self.view_resumen.winfo_children():
            w.destroy()

        frame_top = ctk.CTkFrame(self.view_resumen, fg_color="transparent")
        frame_top.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(frame_top, text="📊 RESUMEN Y ARQUEO DIARIO", font=("Roboto", 22, "bold")).pack(side="left")

        btn_pdf = ctk.CTkButton(
            frame_top, text="📄 EXPORTAR PDF", font=("Roboto", 13, "bold"),
            fg_color="#DC2626", hover_color="#991B1B", height=35, command=self._exportar_resumen_pdf
        )
        btn_pdf.pack(side="right", padx=5)

        hoy = datetime.now().strftime("%Y-%m-%d")
        tot_ventas, tot_efectivo, tot_tarjeta = db.obtener_resumen_dia(hoy)

        frame_cards = ctk.CTkFrame(self.view_resumen, fg_color="transparent")
        frame_cards.pack(padx=20, pady=20)

        cards = [
            ("TOTAL VENTAS HOY", f"${tot_ventas:,.0f}", "#10B981"),
            ("EFECTIVO EN CAJA", f"${tot_efectivo:,.0f}", "#3B82F6"),
            ("DÉBITO / TRANSF.", f"${tot_tarjeta:,.0f}", "#8B5CF6")
        ]

        for tit, val, col in cards:
            c = ctk.CTkFrame(frame_cards, fg_color="#1F2937", width=220, height=120, corner_radius=10)
            c.pack(side="left", padx=15)
            c.pack_propagate(False)
            ctk.CTkLabel(c, text=tit, font=("Roboto", 13, "bold"), text_color="#9CA3AF").pack(pady=(15,5))
            ctk.CTkLabel(c, text=val, font=("Roboto", 24, "bold"), text_color=col).pack()

    # NAVEGACIÓN
    def _ocultar_vistas(self):
        self.view_terminal.grid_forget()
        self.view_inventario.grid_forget()
        self.view_letreros.grid_forget()
        self.view_historial.grid_forget()
        self.view_resumen.grid_forget()

    def _mostrar_terminal(self):
        self._ocultar_vistas()
        self.view_terminal.grid(row=0, column=0, sticky="nsew")

    def _mostrar_inventario(self):
        self._ocultar_vistas()
        self._construir_vista_inventario()
        self.view_inventario.grid(row=0, column=0, sticky="nsew")

    def _mostrar_letreros(self):
        self._ocultar_vistas()
        self._construir_vista_letreros()
        self.view_letreros.grid(row=0, column=0, sticky="nsew")

    def _mostrar_historial(self):
        self._ocultar_vistas()
        self._construir_vista_historial()
        self.view_historial.grid(row=0, column=0, sticky="nsew")

    def _mostrar_resumen(self):
        self._ocultar_vistas()
        self._construir_vista_resumen()
        self.view_resumen.grid(row=0, column=0, sticky="nsew")


if __name__ == "__main__":
    app = POSApp()
    app.mainloop()