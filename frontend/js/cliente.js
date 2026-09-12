/*
  Mercado VIVA — Lógica del módulo cliente
  ------------------------------------------------------------
  Todo el estado vive en memoria + localStorage (token de sesión
  y carrito), y se comunica con el backend vía fetch() a /api/*.
*/

const API = ""; // mismo origen: FastAPI sirve la API y el frontend juntos

// ---------------------------------------------------------------
// Estado
// ---------------------------------------------------------------
let sedes = [];
let sedeActualId = null;
let categoriaActual = "";
let productos = [];
let carrito = JSON.parse(localStorage.getItem("mv_carrito") || "[]");
let token = localStorage.getItem("mv_token");
let usuario = JSON.parse(localStorage.getItem("mv_usuario") || "null");

// ---------------------------------------------------------------
// Utilidades
// ---------------------------------------------------------------
function formatoPrecio(valor) {
  return new Intl.NumberFormat("es-CO", { style: "currency", currency: "COP", maximumFractionDigits: 0 }).format(valor);
}

function guardarCarrito() {
  localStorage.setItem("mv_carrito", JSON.stringify(carrito));
}

function guardarSesion() {
  if (token) {
    localStorage.setItem("mv_token", token);
    localStorage.setItem("mv_usuario", JSON.stringify(usuario));
  } else {
    localStorage.removeItem("mv_token");
    localStorage.removeItem("mv_usuario");
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
    error.data = data;
    throw error;
  }
  return data;
}

function abrirModal(id) {
  document.getElementById(id).classList.add("visible");
}
function cerrarModal(id) {
  document.getElementById(id).classList.remove("visible");
}

document.querySelectorAll("[data-cerrar-modal]").forEach((btn) => {
  btn.addEventListener("click", () => cerrarModal(btn.dataset.cerrarModal));
});

// ---------------------------------------------------------------
// Sedes
// ---------------------------------------------------------------
async function cargarSedes() {
  sedes = await apiFetch("/api/auth/sedes");
  const select = document.getElementById("select-sede");
  select.innerHTML = sedes.map((s) => `<option value="${s.id}">${s.nombre}</option>`).join("");

  const guardada = localStorage.getItem("mv_sede_id");
  sedeActualId = guardada && sedes.some(s => String(s.id) === guardada)
    ? parseInt(guardada, 10)
    : sedes[0]?.id;

  select.value = sedeActualId;
  select.addEventListener("change", () => {
    sedeActualId = parseInt(select.value, 10);
    localStorage.setItem("mv_sede_id", sedeActualId);
    carrito = []; // el carrito es por sede: no mezclar inventarios de sedes distintas
    guardarCarrito();
    actualizarCarritoUI();
    cargarCatalogo();
  });
}

// ---------------------------------------------------------------
// Catálogo
// ---------------------------------------------------------------
async function cargarCatalogo() {
  const params = new URLSearchParams({ sede_id: sedeActualId });
  if (categoriaActual) params.set("categoria", categoriaActual);

  const q = document.getElementById("input-busqueda").value.trim();
  if (q) params.set("q", q);

  productos = await apiFetch(`/api/productos?${params.toString()}`);
  renderizarCategorias();
  renderizarProductos();
}

function renderizarCategorias() {
  const categorias = [...new Set(productos.map((p) => p.categoria))];
  const contenedor = document.getElementById("filtros-categoria");
  contenedor.innerHTML = `<button class="chip ${categoriaActual === "" ? "activo" : ""}" data-categoria="">Todas</button>`
    + categorias.map((c) => `<button class="chip ${categoriaActual === c ? "activo" : ""}" data-categoria="${c}">${c}</button>`).join("");

  contenedor.querySelectorAll(".chip").forEach((chip) => {
    chip.addEventListener("click", () => {
      categoriaActual = chip.dataset.categoria;
      cargarCatalogo();
    });
  });
}

function renderizarProductos() {
  const grid = document.getElementById("grid-productos");

  if (productos.length === 0) {
    grid.innerHTML = `<div class="estado-vacio">No encontramos productos con ese criterio en esta sede.</div>`;
    return;
  }

  grid.innerHTML = productos.map((p) => `
    <article class="tarjeta-producto">
      <div class="tarjeta-producto__imagen">
        <img src="${p.imagen_url || ''}" alt="${p.nombre}" loading="lazy"
             onerror="this.style.display='none'">
      </div>
      <div class="tarjeta-producto__cuerpo">
        <span class="tarjeta-producto__categoria">${p.categoria}</span>
        <p class="tarjeta-producto__nombre">${p.nombre}</p>
        <span class="tarjeta-producto__precio">${formatoPrecio(p.precio)}</span>
        <span class="tarjeta-producto__stock ${p.cantidad === 0 ? 'agotado' : ''}">
          ${p.cantidad === 0 ? 'Sin stock en esta sede' : `${p.cantidad} disponibles`}
        </span>
        <div class="tarjeta-producto__accion">
          <button class="btn ${p.cantidad === 0 ? 'btn--secundario' : 'btn--primario'}"
                  data-agregar="${p.id}" ${p.cantidad === 0 ? 'disabled' : ''}>
            ${p.cantidad === 0 ? 'Agotado' : 'Agregar al carrito'}
          </button>
        </div>
      </div>
    </article>
  `).join("");

  grid.querySelectorAll("[data-agregar]").forEach((btn) => {
    btn.addEventListener("click", () => agregarAlCarrito(parseInt(btn.dataset.agregar, 10)));
  });
}

document.getElementById("btn-buscar").addEventListener("click", cargarCatalogo);
document.getElementById("input-busqueda").addEventListener("keydown", (e) => {
  if (e.key === "Enter") cargarCatalogo();
});
document.getElementById("btn-hero-explorar").addEventListener("click", () => {
  document.querySelector(".catalogo").scrollIntoView({ behavior: "smooth" });
});

// ---------------------------------------------------------------
// Carrito
// ---------------------------------------------------------------
function agregarAlCarrito(productoId) {
  const producto = productos.find((p) => p.id === productoId);
  if (!producto) return;

  const existente = carrito.find((i) => i.producto_id === productoId);
  if (existente) {
    existente.cantidad += 1;
  } else {
    carrito.push({
      producto_id: producto.id,
      nombre: producto.nombre,
      precio: producto.precio,
      imagen_url: producto.imagen_url,
      cantidad: 1,
    });
  }
  guardarCarrito();
  actualizarCarritoUI();
  abrirPanelCarrito();
}

function cambiarCantidad(productoId, delta) {
  const item = carrito.find((i) => i.producto_id === productoId);
  if (!item) return;
  item.cantidad += delta;
  if (item.cantidad <= 0) {
    carrito = carrito.filter((i) => i.producto_id !== productoId);
  }
  guardarCarrito();
  actualizarCarritoUI();
}

function quitarDelCarrito(productoId) {
  carrito = carrito.filter((i) => i.producto_id !== productoId);
  guardarCarrito();
  actualizarCarritoUI();
}

function totalCarrito() {
  return carrito.reduce((acc, i) => acc + i.precio * i.cantidad, 0);
}

function actualizarCarritoUI() {
  const contador = document.getElementById("carrito-contador");
  const totalItems = carrito.reduce((acc, i) => acc + i.cantidad, 0);
  contador.style.display = totalItems > 0 ? "flex" : "none";
  contador.textContent = totalItems;

  const contenedor = document.getElementById("carrito-items");
  if (carrito.length === 0) {
    contenedor.innerHTML = `<div class="estado-vacio">Tu carrito está vacío.</div>`;
  } else {
    contenedor.innerHTML = carrito.map((i) => `
      <div class="item-carrito">
        <div class="item-carrito__imagen"><img src="${i.imagen_url || ''}" onerror="this.style.display='none'"></div>
        <div class="item-carrito__info">
          <p class="item-carrito__nombre">${i.nombre}</p>
          <div class="item-carrito__controles">
            <button data-menos="${i.producto_id}">−</button>
            <span>${i.cantidad}</span>
            <button data-mas="${i.producto_id}">+</button>
            <span style="margin-left:8px;">${formatoPrecio(i.precio * i.cantidad)}</span>
            <button class="item-carrito__quitar" data-quitar="${i.producto_id}">Quitar</button>
          </div>
        </div>
      </div>
    `).join("");

    contenedor.querySelectorAll("[data-mas]").forEach((b) => b.addEventListener("click", () => cambiarCantidad(parseInt(b.dataset.mas), 1)));
    contenedor.querySelectorAll("[data-menos]").forEach((b) => b.addEventListener("click", () => cambiarCantidad(parseInt(b.dataset.menos), -1)));
    contenedor.querySelectorAll("[data-quitar]").forEach((b) => b.addEventListener("click", () => quitarDelCarrito(parseInt(b.dataset.quitar))));
  }

  document.getElementById("carrito-total").textContent = formatoPrecio(totalCarrito());
}

function abrirPanelCarrito() {
  document.getElementById("panel-carrito").classList.add("visible");
  document.getElementById("overlay").classList.add("visible");
}
function cerrarPanelCarrito() {
  document.getElementById("panel-carrito").classList.remove("visible");
  document.getElementById("overlay").classList.remove("visible");
}

document.getElementById("btn-carrito").addEventListener("click", abrirPanelCarrito);
document.getElementById("btn-cerrar-carrito").addEventListener("click", cerrarPanelCarrito);
document.getElementById("overlay").addEventListener("click", cerrarPanelCarrito);

// ---------------------------------------------------------------
// Autenticación (login / registro)
// ---------------------------------------------------------------
function actualizarUIsesion() {
  const btnCuenta = document.getElementById("btn-cuenta");
  const btnPedidos = document.getElementById("btn-mis-pedidos");
  if (usuario) {
    btnCuenta.textContent = `Hola, ${usuario.nombres}`;
    btnPedidos.style.display = "inline-block";
  } else {
    btnCuenta.textContent = "Iniciar sesión";
    btnPedidos.style.display = "none";
  }
}

document.getElementById("btn-cuenta").addEventListener("click", () => {
  if (usuario) {
    if (confirm("¿Cerrar sesión?")) {
      token = null;
      usuario = null;
      guardarSesion();
      actualizarUIsesion();
    }
  } else {
    abrirModal("modal-cuenta");
  }
});

document.querySelectorAll("#modal-cuenta .tabs button").forEach((tab) => {
  tab.addEventListener("click", () => {
    document.querySelectorAll("#modal-cuenta .tabs button").forEach((t) => t.classList.remove("activo"));
    tab.classList.add("activo");
    document.getElementById("form-login").style.display = tab.dataset.tab === "login" ? "block" : "none";
    document.getElementById("form-registro").style.display = tab.dataset.tab === "registro" ? "block" : "none";
    document.getElementById("error-cuenta").classList.remove("visible");
  });
});

document.getElementById("form-login").addEventListener("submit", async (e) => {
  e.preventDefault();
  const errorBox = document.getElementById("error-cuenta");
  errorBox.classList.remove("visible");
  try {
    const data = await apiFetch("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({
        email: document.getElementById("login-email").value,
        password: document.getElementById("login-password").value,
      }),
    });
    if (data.usuario.tipo !== "cliente") {
      errorBox.textContent = "Esta cuenta es de administrador. Usa el panel admin.";
      errorBox.classList.add("visible");
      return;
    }
    token = data.access_token;
    usuario = data.usuario;
    guardarSesion();
    actualizarUIsesion();
    cerrarModal("modal-cuenta");
  } catch (err) {
    errorBox.textContent = err.message;
    errorBox.classList.add("visible");
  }
});

document.getElementById("form-registro").addEventListener("submit", async (e) => {
  e.preventDefault();
  const errorBox = document.getElementById("error-cuenta");
  errorBox.classList.remove("visible");
  try {
    const data = await apiFetch("/api/auth/registro/cliente", {
      method: "POST",
      body: JSON.stringify({
        nombres: document.getElementById("reg-nombres").value,
        apellidos: document.getElementById("reg-apellidos").value,
        email: document.getElementById("reg-email").value,
        documento: document.getElementById("reg-documento").value,
        telefono: document.getElementById("reg-telefono").value || null,
        direccion: document.getElementById("reg-direccion").value || null,
        ciudad: document.getElementById("reg-ciudad").value || null,
        password: document.getElementById("reg-password").value,
      }),
    });
    token = data.access_token;
    usuario = data.usuario;
    guardarSesion();
    actualizarUIsesion();
    cerrarModal("modal-cuenta");
  } catch (err) {
    errorBox.textContent = err.message;
    errorBox.classList.add("visible");
  }
});

// ---------------------------------------------------------------
// Checkout
// ---------------------------------------------------------------
document.getElementById("btn-ir-a-pagar").addEventListener("click", () => {
  if (carrito.length === 0) return;
  if (!usuario) {
    cerrarPanelCarrito();
    abrirModal("modal-cuenta");
    return;
  }
  // Precarga los datos de residencia del perfil, si existen
  if (usuario.direccion) document.getElementById("chk-direccion-envio").value = usuario.direccion;
  if (usuario.ciudad) document.getElementById("chk-ciudad-envio").value = usuario.ciudad;
  document.getElementById("chk-nombre-fact").value = `${usuario.nombres} ${usuario.apellidos}`;
  document.getElementById("chk-doc-fact").value = usuario.documento;
  document.getElementById("chk-telefono").value = usuario.telefono || "";

  document.getElementById("checkout-total").textContent = formatoPrecio(totalCarrito());
  cerrarPanelCarrito();
  abrirModal("modal-checkout");
});

document.getElementById("form-checkout").addEventListener("submit", async (e) => {
  e.preventDefault();
  const errorBox = document.getElementById("error-checkout");
  errorBox.classList.remove("visible");

  const payload = {
    sede_id: sedeActualId,
    items: carrito.map((i) => ({ producto_id: i.producto_id, cantidad: i.cantidad })),
    nombre_facturacion: document.getElementById("chk-nombre-fact").value,
    documento_facturacion: document.getElementById("chk-doc-fact").value,
    direccion_facturacion: document.getElementById("chk-direccion-fact").value,
    ciudad_facturacion: document.getElementById("chk-ciudad-fact").value,
    direccion_envio: document.getElementById("chk-direccion-envio").value,
    ciudad_envio: document.getElementById("chk-ciudad-envio").value,
    telefono_contacto: document.getElementById("chk-telefono").value,
  };

  try {
    const data = await apiFetch("/api/cliente/checkout", { method: "POST", body: JSON.stringify(payload) });

    if (data.resultado === "sin_stock") {
      cerrarModal("modal-checkout");
      mostrarAlternativas(data.items_sin_stock);
      return;
    }

    // Confirmado
    carrito = [];
    guardarCarrito();
    actualizarCarritoUI();
    cerrarModal("modal-checkout");
    alert(`¡Pedido #${data.pedido.id} confirmado! Total: ${formatoPrecio(data.pedido.total)}`);
    cargarCatalogo(); // refresca el stock mostrado
  } catch (err) {
    errorBox.textContent = err.message;
    errorBox.classList.add("visible");
  }
});

function mostrarAlternativas(itemsSinStock) {
  const lista = document.getElementById("alternativas-lista");
  const mensaje = document.getElementById("alternativas-mensaje");

  const nombres = itemsSinStock.map((i) => i.producto_nombre).join(", ");
  mensaje.textContent = `No pudimos completar tu compra porque no hay stock suficiente de: ${nombres}. No se realizó ningún cobro. Estas son algunas alternativas:`;

  let html = "";
  itemsSinStock.forEach((item) => {
    if (item.alternativas.length === 0) {
      html += `<p style="font-size:0.85rem;">No encontramos alternativas para <strong>${item.producto_nombre}</strong> en este momento.</p>`;
    }
    item.alternativas.forEach((alt) => {
      const etiqueta = alt.tipo_alternativa === "otra_sede_mismo_producto" ? `Disponible en ${alt.sede_nombre}` : "Producto similar";
      html += `
        <div class="alternativa-item">
          <div class="alternativa-item__imagen"><img src="${alt.imagen_url || ''}" onerror="this.style.display='none'"></div>
          <div class="alternativa-item__info">
            <span class="alternativa-item__etiqueta">${etiqueta}</span>
            <p style="margin:0; font-weight:600; font-size:0.85rem;">${alt.nombre}</p>
            <span style="font-size:0.8rem; color:var(--color-texto-suave);">${formatoPrecio(alt.precio)} · ${alt.cantidad} disponibles</span>
          </div>
        </div>
      `;
    });
  });
  lista.innerHTML = html;
  abrirModal("modal-alternativas");
}

// ---------------------------------------------------------------
// Mis pedidos (historial)
// ---------------------------------------------------------------
document.getElementById("btn-mis-pedidos").addEventListener("click", async () => {
  const contenedor = document.getElementById("lista-pedidos");
  try {
    const pedidos = await apiFetch("/api/cliente/pedidos");
    if (pedidos.length === 0) {
      contenedor.innerHTML = `<div class="estado-vacio">Aún no tienes pedidos.</div>`;
    } else {
      contenedor.innerHTML = pedidos.map((p) => `
        <div class="pedido-card">
          <div class="pedido-card__header">
            <strong>Pedido #${p.id}</strong>
            <span class="pedido-card__estado">${p.estado}</span>
          </div>
          ${p.items.map((it) => `
            <div class="pedido-card__item">
              <span>${it.cantidad} × ${it.producto_nombre}</span>
              <span>${formatoPrecio(it.precio_unitario * it.cantidad)}</span>
            </div>
          `).join("")}
          <div class="pedido-card__item" style="font-weight:700; color:var(--color-texto); margin-top:6px;">
            <span>Total</span><span>${formatoPrecio(p.total)}</span>
          </div>
          <div style="font-size:0.75rem; color:var(--color-texto-suave); margin-top:6px;">
            Entrega en: ${p.direccion_envio}, ${p.ciudad_envio}
          </div>
        </div>
      `).join("");
    }
    abrirModal("modal-pedidos");
  } catch (err) {
    alert(err.message);
  }
});

// ---------------------------------------------------------------
// Inicio
// ---------------------------------------------------------------
(async function init() {
  actualizarUIsesion();
  actualizarCarritoUI();
  await cargarSedes();
  await cargarCatalogo();
})();
