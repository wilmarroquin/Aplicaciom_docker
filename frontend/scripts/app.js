const API_URL = 'https://aplicaciom-docker.onrender.com';

let customersCache = [];
let zonesCache = [];
let editingAddressId = null;
let map;
let markerLayer;
const addressMarkers = new Map();

const appView = document.getElementById('appView');
const appStatusPanel = document.getElementById('appStatusPanel');
const appStatus = document.getElementById('appStatus');
const customerList = document.getElementById('customerList');
const addressList = document.getElementById('addressList');
const mapStatus = document.getElementById('mapStatus');
const addressSubmit = document.getElementById('addressSubmit');
const cancelAddressEdit = document.getElementById('cancelAddressEdit');

function setAppStatus(message) {
    const formattedMessage = message ? formatErrorDetail(message) : '';
    appStatus.textContent = formattedMessage;
    appStatusPanel.hidden = !formattedMessage;
}

function setMapStatus(message) {
    mapStatus.textContent = message || '';
}

function formatErrorDetail(detail) {
    if (!detail) {
        return 'No se pudo completar la operación';
    }

    if (typeof detail === 'string') {
        return detail;
    }

    if (Array.isArray(detail)) {
        return detail
            .map((item) => item.msg || item.message || JSON.stringify(item))
            .join('. ');
    }

    if (typeof detail === 'object') {
        return detail.msg || detail.message || JSON.stringify(detail);
    }

    return String(detail);
}

function fallbackErrorMessage(statusCode) {
    const messages = {
        401: 'Sesión inválida o expirada. Inicia sesión nuevamente.',
        403: 'No tienes permisos para realizar esta acción.',
        404: 'El recurso solicitado no existe.',
        422: 'Revisa los datos ingresados.',
        500: 'Error interno del servidor.'
    };

    return messages[statusCode] || `Error HTTP ${statusCode}`;
}

function findCustomerName(customerId) {
    const customer = customersCache.find((item) => item.id === customerId);
    return customer ? customer.full_name : `Cliente #${customerId}`;
}

function findZoneName(zoneId) {
    const zone = zonesCache.find((item) => item.id === zoneId);
    return zone ? zone.name : `Zona #${zoneId}`;
}

async function apiFetch(path, options = {}) {
    let response;

    const url = path.startsWith('http')
        ? path
        : `${API_URL}${path}`;

    console.log('Consultando API:', url);

    try {
        response = await fetch(url, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...(options.headers || {})
            }
        });
    } catch {
        throw new Error('No se pudo conectar con la API. Verifica que el backend esté disponible en Render.');
    }

    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: fallbackErrorMessage(response.status) }));
        throw new Error(formatErrorDetail(error.detail) || fallbackErrorMessage(response.status));
    }

    return response.json().catch(() => ({}));
}

function showAppView() {
    appView.hidden = false;
    ensureMap();
    setTimeout(() => map?.invalidateSize(), 0);
    window.scrollTo(0, 0);
}

function ensureMap() {
    if (appView.hidden) {
        return null;
    }

    if (!window.L) {
        setMapStatus('No se pudo cargar la librería del mapa.');
        return null;
    }

    if (!map) {
        map = L.map('map').setView([14.6349, -90.5133], 13);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 19,
            attribution: '&copy; OpenStreetMap'
        }).addTo(map);
        markerLayer = L.layerGroup().addTo(map);
    }

    return map;
}

function fitMapToMarkers() {
    if (!markerLayer || markerLayer.getLayers().length === 0) {
        return;
    }

    const bounds = L.latLngBounds(markerLayer.getLayers().map((marker) => marker.getLatLng()));
    map.fitBounds(bounds, { padding: [24, 24] });
}

function locateAddress(addressId) {
    const marker = addressMarkers.get(addressId);
    if (!marker || !map) {
        setMapStatus('No se pudo localizar la dirección en el mapa.');
        return;
    }

    const position = marker.getLatLng();
    map.setView(position, Math.max(map.getZoom(), 16), { animate: true });
    marker.openPopup();
    document.getElementById('map').scrollIntoView({ behavior: 'smooth', block: 'center' });
}

function renderCustomers(customers) {
    const customerSelect = document.getElementById('addressCustomer');
    customerList.replaceChildren();
    customerSelect.replaceChildren(new Option('Cliente', ''));

    customers.forEach((customer) => {
        const item = document.createElement('li');
        item.textContent = `${customer.full_name} - ${customer.phone}`;
        customerList.appendChild(item);
        customerSelect.appendChild(new Option(customer.full_name, customer.id));
    });
}

function renderZones(zones) {
    const zoneSelect = document.getElementById('addressZone');
    zoneSelect.replaceChildren(new Option('Zona', ''));

    zones.forEach((zone) => {
        zoneSelect.appendChild(new Option(`${zone.name} (${zone.municipality})`, zone.id));
    });
}

function createAddressPopup(customerName, streetAddress, zoneName) {
    const wrapper = document.createElement('div');
    const title = document.createElement('strong');
    title.textContent = customerName;
    wrapper.appendChild(title);
    wrapper.appendChild(document.createElement('br'));
    wrapper.appendChild(document.createTextNode(streetAddress));
    wrapper.appendChild(document.createElement('br'));
    wrapper.appendChild(document.createTextNode(zoneName));
    return wrapper;
}

function fillAddressForm(address) {
    editingAddressId = address.id;
    document.getElementById('addressCustomer').value = address.customer_id;
    document.getElementById('addressZone').value = address.zone_id;
    document.getElementById('streetAddress').value = address.street_address;
    document.getElementById('referenceNote').value = address.reference_note || '';
    document.getElementById('latitude').value = address.latitude;
    document.getElementById('longitude').value = address.longitude;
    document.getElementById('isDefaultAddress').checked = address.is_default;
    addressSubmit.textContent = 'Actualizar dirección';
    cancelAddressEdit.hidden = false;
    setAppStatus('');
}

function resetAddressForm(form) {
    editingAddressId = null;
    form.reset();
    addressSubmit.textContent = 'Guardar dirección';
    cancelAddressEdit.hidden = true;
}

function renderAddresses(addresses) {
    const currentMap = ensureMap();
    addressList.replaceChildren();
    markerLayer?.clearLayers();
    addressMarkers.clear();
    setMapStatus('');

    if (addresses.length === 0) {
        setMapStatus('No hay direcciones registradas para mostrar en el mapa.');
        return;
    }

    addresses.forEach((address) => {
        const lat = Number(address.latitude);
        const lon = Number(address.longitude);
        const customerName = findCustomerName(address.customer_id);
        const zoneName = findZoneName(address.zone_id);

        const item = document.createElement('li');
        const editButton = document.createElement('button');
        const locateButton = document.createElement('button');
        editButton.type = 'button';
        editButton.textContent = 'Editar';
        editButton.addEventListener('click', () => fillAddressForm(address));
        locateButton.type = 'button';
        locateButton.textContent = 'Localizar';
        locateButton.addEventListener('click', () => locateAddress(address.id));

        item.textContent = `${customerName} - ${address.street_address} (${lat}, ${lon}) `;
        item.appendChild(locateButton);
        item.appendChild(editButton);
        addressList.appendChild(item);

        if (currentMap && Number.isFinite(lat) && Number.isFinite(lon)) {
            const marker = L.marker([lat, lon])
                .bindPopup(createAddressPopup(customerName, address.street_address, zoneName))
                .addTo(markerLayer);
            addressMarkers.set(address.id, marker);
        } else {
            locateButton.disabled = true;
        }
    });

    setMapStatus(`${addresses.length} ubicacion(es) cargada(s).`);
    fitMapToMarkers();
}

async function loadCustomers() {
    customersCache = await apiFetch('/api/customers')   ;
    renderCustomers(customersCache);
}

async function loadZones() {
    zonesCache = await apiFetch('/api/zones');
    renderZones(zonesCache);
}

async function loadAddresses() {
    const addresses = await apiFetch('/api/addresses');
    renderAddresses(addresses);
}

async function refreshOperationalData() {
    await loadCustomers();
    await loadZones();
    await loadAddresses();
}

async function openApplication() {
    showAppView();
    setAppStatus('');
    await refreshOperationalData();
}

document.getElementById('customerForm').addEventListener('submit', async (event) => {
    event.preventDefault();
    try {
        await apiFetch('/api/customers', {
            method: 'POST',
            body: JSON.stringify({
                full_name: document.getElementById('customerName').value,
                phone: document.getElementById('customerPhone').value,
                email: document.getElementById('customerEmail').value || null,
                notes: document.getElementById('customerNotes').value || null
            })
        });
        event.target.reset();
        setAppStatus('Cliente guardado correctamente');
        await loadCustomers();
    } catch (error) {
        setAppStatus(error.message);
    }
});

document.getElementById('addressForm').addEventListener('submit', async (event) => {
    event.preventDefault();
    try {
        const wasEditing = Boolean(editingAddressId);
        const path = editingAddressId ? `/api/addresses/${editingAddressId}` : '/api/addresses';
        const method = editingAddressId ? 'PUT' : 'POST';

        await apiFetch(path, {
            method,
            body: JSON.stringify({
                customer_id: Number(document.getElementById('addressCustomer').value),
                zone_id: Number(document.getElementById('addressZone').value),
                street_address: document.getElementById('streetAddress').value,
                reference_note: document.getElementById('referenceNote').value || null,
                latitude: Number(document.getElementById('latitude').value),
                longitude: Number(document.getElementById('longitude').value),
                is_default: document.getElementById('isDefaultAddress').checked
            })
        });
        resetAddressForm(event.target);
        setAppStatus(wasEditing ? 'Dirección actualizada correctamente' : 'Dirección guardada correctamente');
        await loadAddresses();
    } catch (error) {
        setAppStatus(error.message);
    }
});

cancelAddressEdit.addEventListener('click', () => {
    resetAddressForm(document.getElementById('addressForm'));
    setAppStatus('');
});

document.getElementById('loadCustomers').addEventListener('click', async () => {
    try {
        await loadCustomers();
    } catch (error) {
        setAppStatus(error.message);
    }
});

document.getElementById('loadAddresses').addEventListener('click', async () => {
    try {
        await refreshOperationalData();
    } catch (error) {
        setAppStatus(error.message);
    }
});

document.getElementById('fitMap').addEventListener('click', fitMapToMarkers);

openApplication().catch((error) => setAppStatus(error.message));
