/*
  Mercado VIVA — Lógica del panel administrador
*/

const API = "";

let token = localStorage.getItem("mv_admin_token");
let admin = JSON.parse(localStorage.getItem("mv_admin_usuario") || "null");
let inventario = [];

function guardarSesionAdmin() {
  if (token) {
    localStorage.setItem("mv_admin_token", token);
    localStorage.setItem("mv_admin_usuario", JSON.stringify(admin));
  } else {
    localStorage.removeItem("mv_admin_token");
    localStorage.removeItem("mv_admin_usuario");
  }
}

async function apiFetch(ruta, opciones = {}) {
  const headers = { "Content-Type": "application/json", ...(opciones.headers || {}) };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const res = await fetch(API + ruta, { ...opciones, headers });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const error = new Error(data.detail || "Ocurrió un error inesperado");
    error.status = res.status;
    throw error;
  }
  return data;
}

function formatoPrecio(valor) {
  return new Intl.NumberFormat("es-CO", { style: "currency", currency: "COP", maximumFractionDigits: 0 }).format(valor);
}

// ---------------------------------------------------------------
// Login / Registro
// ---------------------------------------------------------------

document.querySelectorAll(".tabs-admin button").forEach((tab) => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".tabs-admin button").forEach((t) => t.classList.remove("activo"));
    tab.classList.add("activo");
    document.getElementById("form-login-admin").style.display = tab.dataset.tab === "login" ? "block" : "none";
    document.getElementById("form-registro-admin").style.display = tab.dataset.tab === "registro" ? "block" : "none";
    document.getElementById("error-login-admin").classList.remove("visible");
  });
});

async function cargarSedesParaRegistro() {
  try {
    const sedes = await apiFetch("/api/auth/sedes");
    const select = document.getElementById("admin-reg-sede");
    select.innerHTML = sedes.map((s) => `<option value="${s.id}">${s.nombre} — ${s.ciudad}</option>`).join("");
  } catch (err) {
    console.error("No se pudieron cargar las sedes", err);
  }
}

document.getElementById("form-login-admin").addEventListener("submit", async (e) => {
  e.preventDefault();
  const errorBox = document.getElementById("error-login-admin");
  errorBox.classList.remove("visible");
  try {
    const data = await apiFetch("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({
        email: document.getElementById("admin-login-email").value,
        password: document.getElementById("admin-login-password").value,
      }),
    });
    if (data.usuario.tipo !== "admin") {
      errorBox.textContent = "Esta cuenta es de cliente. Usa la tienda.";
      errorBox.classList.add("visible");
      return;
    }
    token = data.access_token;
    admin = data.usuario;
    guardarSesionAdmin();
    mostrarDashboard();
  } catch (err) {
    errorBox.textContent = err.message;
    errorBox.classList.add("visible");
  }
});

document.getElementById("form-registro-admin").addEventListener("submit", async (e) => {
  e.preventDefault();
  const errorBox = document.getElementById("error-login-admin");
  errorBox.classList.remove("visible");
  try {
    const data = await apiFetch("/api/auth/registro/admin", {
      method: "POST",
      body: JSON.stringify({
        nombres: document.getElementById("admin-reg-nombres").value,
        apellidos: document.getElementById("admin-reg-apellidos").value,
        email: document.getElementById("admin-reg-email").value,
        documento: document.getElementById("admin-reg-documento").value,
        telefono: document.getElementById("admin-reg-telefono").value || null,
        sede_id: parseInt(document.getElementById("admin-reg-sede").value, 10),
        password: document.getElementById("admin-reg-password").value,
      }),
    });
    token = data.access_token;
    admin = data.usuario;
    guardarSesionAdmin();
    mostrarDashboard();
  } catch (err) {
    errorBox.textContent = err.message;
    errorBox.classList.add("visible");
  }
});

document.getElementById("btn-cerrar-sesion-admin").addEventListener("click", () => {
  token = null;
  admin = null;
  guardarSesionAdmin();
  document.getElementById("dashboard").classList.remove("activo");
  document.getElementById("pantalla-login").style.display = "flex";
});

// ---------------------------------------------------------------
// Navegación del dashboard
// ---------------------------------------------------------------

document.querySelectorAll(".sidebar__nav button").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".sidebar__nav button").forEach((b) => b.classList.remove("activo"));
    btn.classList.add("activo");
    document.querySelectorAll(".vista").forEach((v) => v.classList.remove("activa"));
    document.getElementById(`vista-${btn.dataset.vista}`).classList.add("activa");
  });
});

async function mostrarDashboard() {
  document.getElementById("pantalla-login").style.display = "none";
  document.getElementById("dashboard").classList.add("activo");
  document.getElementById("admin-usuario-label").textContent = `// sesión: ${admin.nombres} ${admin.apellidos} · ${admin.email}`;

  try {
    const sedes = await apiFetch("/api/auth/sedes");
    const miSede = sedes.find((s) => s.id === admin.sede_id);
    document.getElementById("sidebar-sede-nombre").textContent = miSede ? miSede.nombre : `Sede #${admin.sede_id}`;
  } catch {
    document.getElementById("sidebar-sede-nombre").textContent = `Sede #${admin.sede_id}`;
  }

  cargarInventario();
}

// ---------------------------------------------------------------
// Inventario
// ---------------------------------------------------------------

async function cargarInventario() {
  try {
    inventario = await apiFetch("/api/admin/inventario");
    renderizarInventario();
    renderizarKPIs();
  } catch (err) {
    mostrarMensaje("mensaje-inventario", err.message, "error");
  }
}

function renderizarKPIs() {
  const activos = inventario.filter((p) => p.activo);
  const unidades = activos.reduce((acc, p) => acc + p.cantidad, 0);
  const agotados = activos.filter((p) => p.cantidad === 0).length;
  const valor = activos.reduce((acc, p) => acc + p.cantidad * p.precio, 0);

  document.getElementById("kpi-total").textContent = activos.length;
  document.getElementById("kpi-unidades").textContent = unidades;
  document.getElementById("kpi-agotados").textContent = agotados;
  document.getElementById("kpi-valor").textContent = formatoPrecio(valor);
}

function renderizarInventario() {
  const cuerpo = document.getElementById("tabla-inventario-body");
  const activos = inventario.filter((p) => p.activo);

  if (activos.length === 0) {
    cuerpo.innerHTML = `<tr><td colspan="8" style="text-align:center; padding:30px; color:var(--color-texto-suave);">Aún no hay productos en tu sede. Agrega el primero desde el menú "Agregar producto".</td></tr>`;
    return;
  }

  cuerpo.innerHTML = activos.map((p) => {
    let claseBadge = "";
    let textoBadge = `${p.cantidad} und`;
    if (p.cantidad === 0) { claseBadge = "agotado"; textoBadge = "agotado"; }
    else if (p.cantidad <= 5) { claseBadge = "bajo"; }

    return `
      <tr data-fila="${p.id}">
        <td><img class="miniatura" src="${p.imagen_url || ''}" onerror="this.style.visibility='hidden'"></td>
        <td class="celda-sku">${p.sku}</td>
        <td>${p.nombre}</td>
        <td>${p.categoria}</td>
        <td class="mono">${formatoPrecio(p.precio)}</td>
        <td>
          <input type="number" class="input-cantidad-inline" min="0" value="${p.cantidad}" data-input-cantidad="${p.id}">
        </td>
        <td><span class="badge-stock ${claseBadge}">${textoBadge}</span></td>
        <td>
          <div class="acciones-fila">
            <button class="btn-fila btn-fila--guardar" data-guardar="${p.id}">Guardar</button>
            <button class="btn-fila btn-fila--editar" data-editar="${p.id}">Editar</button>
            <button class="btn-fila btn-fila--eliminar" data-eliminar="${p.id}">Eliminar</button>
          </div>
        </td>
      </tr>
    `;
  }).join("");

  cuerpo.querySelectorAll("[data-guardar]").forEach((btn) => {
    btn.addEventListener("click", () => guardarCantidad(parseInt(btn.dataset.guardar, 10)));
  });
  cuerpo.querySelectorAll("[data-eliminar]").forEach((btn) => {
    btn.addEventListener("click", () => eliminarProducto(parseInt(btn.dataset.eliminar, 10)));
  });
  cuerpo.querySelectorAll("[data-editar]").forEach((btn) => {
    btn.addEventListener("click", () => abrirModalEditar(parseInt(btn.dataset.editar, 10)));
  });
}

// ---------------------------------------------------------------
// Editar producto (nombre, categoría, precio, cantidad, imagen)
// ---------------------------------------------------------------

function abrirModalEditar(productoId) {
  const producto = inventario.find((p) => p.id === productoId);
  if (!producto) return;

  document.getElementById("edit-producto-id").value = producto.id;
  document.getElementById("edit-sku").value = producto.sku;
  document.getElementById("edit-categoria").value = producto.categoria || "";
  document.getElementById("edit-nombre").value = producto.nombre;
  document.getElementById("edit-descripcion").value = producto.descripcion || "";
  document.getElementById("edit-precio").value = producto.precio;
  document.getElementById("edit-cantidad").value = producto.cantidad;
  document.getElementById("edit-imagen").value = producto.imagen_url || "";

  document.getElementById("mensaje-editar").className = "mensaje-admin";
  document.getElementById("modal-editar-producto").classList.add("visible");
}

function cerrarModalEditar() {
  document.getElementById("modal-editar-producto").classList.remove("visible");
}

document.getElementById("btn-cerrar-editar").addEventListener("click", cerrarModalEditar);
document.getElementById("modal-editar-producto").addEventListener("click", (e) => {
  if (e.target.id === "modal-editar-producto") cerrarModalEditar();
});

document.getElementById("form-editar-producto").addEventListener("submit", async (e) => {
  e.preventDefault();
  const productoId = parseInt(document.getElementById("edit-producto-id").value, 10);

  try {
    await apiFetch(`/api/admin/productos/${productoId}`, {
      method: "PUT",
      body: JSON.stringify({
        nombre: document.getElementById("edit-nombre").value,
        categoria: document.getElementById("edit-categoria").value || "General",
        descripcion: document.getElementById("edit-descripcion").value || null,
        precio: parseFloat(document.getElementById("edit-precio").value),
        cantidad: parseInt(document.getElementById("edit-cantidad").value, 10),
        imagen_url: document.getElementById("edit-imagen").value || null,
      }),
    });
    cerrarModalEditar();
    mostrarMensaje("mensaje-inventario", "Producto actualizado correctamente.", "exito");
    await cargarInventario();
  } catch (err) {
    const el = document.getElementById("mensaje-editar");
    el.textContent = err.message;
    el.className = "mensaje-admin error";
  }
});

async function guardarCantidad(productoId) {
  const input = document.querySelector(`[data-input-cantidad="${productoId}"]`);
  const nuevaCantidad = parseInt(input.value, 10);

  if (isNaN(nuevaCantidad) || nuevaCantidad < 0) {
    mostrarMensaje("mensaje-inventario", "La cantidad debe ser un número válido mayor o igual a 0.", "error");
    return;
  }

  try {
    await apiFetch(`/api/admin/productos/${productoId}`, {
      method: "PUT",
      body: JSON.stringify({ cantidad: nuevaCantidad }),
    });
    mostrarMensaje("mensaje-inventario", "Cantidad actualizada correctamente.", "exito");
    await cargarInventario();
  } catch (err) {
    mostrarMensaje("mensaje-inventario", err.message, "error");
  }
}

async function eliminarProducto(productoId) {
  const producto = inventario.find((p) => p.id === productoId);
  if (!confirm(`¿Eliminar "${producto?.nombre}" del catálogo? Los pedidos ya realizados no se ven afectados.`)) return;

  try {
    await apiFetch(`/api/admin/productos/${productoId}`, { method: "DELETE" });
    mostrarMensaje("mensaje-inventario", "Producto eliminado del catálogo.", "exito");
    await cargarInventario();
  } catch (err) {
    mostrarMensaje("mensaje-inventario", err.message, "error");
  }
}

// ---------------------------------------------------------------
// Agregar producto
// ---------------------------------------------------------------

document.getElementById("form-agregar-producto").addEventListener("submit", async (e) => {
  e.preventDefault();
  try {
    await apiFetch("/api/admin/productos", {
      method: "POST",
      body: JSON.stringify({
        sku: document.getElementById("prod-sku").value,
        nombre: document.getElementById("prod-nombre").value,
        descripcion: document.getElementById("prod-descripcion").value || null,
        categoria: document.getElementById("prod-categoria").value || "General",
        precio: parseFloat(document.getElementById("prod-precio").value),
        cantidad: parseInt(document.getElementById("prod-cantidad").value, 10),
        imagen_url: document.getElementById("prod-imagen").value || null,
      }),
    });
    mostrarMensaje("mensaje-agregar", "Producto agregado al catálogo.", "exito");
    document.getElementById("form-agregar-producto").reset();
    await cargarInventario();
  } catch (err) {
    mostrarMensaje("mensaje-agregar", err.message, "error");
  }
});

// ---------------------------------------------------------------
// Utilidad de mensajes
// ---------------------------------------------------------------

function mostrarMensaje(elementId, texto, tipo) {
  const el = document.getElementById(elementId);
  el.textContent = texto;
  el.className = `mensaje-admin ${tipo}`;
  setTimeout(() => { el.className = "mensaje-admin"; }, 4000);
}

// ---------------------------------------------------------------
// Inicio
// ---------------------------------------------------------------

(async function init() {
  await cargarSedesParaRegistro();
  if (token && admin) {
    mostrarDashboard();
  }
})();