

let map;
let userLocation = null;
let vendorMarkers = [];
let directionsService;
let directionsRenderer;

function initMap() {
    const defaultCenter = { lat: 22.30, lng: 73.19 };

    map = new google.maps.Map(document.getElementById("map"), {
        center: defaultCenter,
        zoom: 13,
    });

    directionsService = new google.maps.DirectionsService();
    directionsRenderer = new google.maps.DirectionsRenderer({
        map: map,
        suppressMarkers: false,
    });

    detectUserLocation();
}

/* ---------------------------------------------
   Detect user's current location
--------------------------------------------- */
function detectUserLocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            (pos) => {
                userLocation = {
                    lat: pos.coords.latitude,
                    lng: pos.coords.longitude,
                };

                map.setCenter(userLocation);

                new google.maps.Marker({
                    map: map,
                    position: userLocation,
                    icon: "http://maps.google.com/mapfiles/ms/icons/blue-dot.png",
                    title: "You are here",
                });

                // Notify backend that user's location is ready
                window.dispatchEvent(
                    new CustomEvent("userLocationReady", {
                        detail: userLocation,
                    })
                );
            },
            () => alert("Location access denied.")
        );
    } else {
        alert("Geolocation not supported.");
    }
}

/* ---------------------------------------------
   Backend will call this function and pass:
   vendors = [
      { id, name, lat, lng, rating }
   ]
--------------------------------------------- */
function computeDistanceAndTimeForVendors(vendors, callback) {
    if (!userLocation) {
        return alert("User location not detected yet.");
    }

    const service = new google.maps.DistanceMatrixService();

    const destinations = vendors.map(v => ({ lat: v.lat, lng: v.lng }));

    service.getDistanceMatrix(
        {
            origins: [userLocation],
            destinations: destinations,
            travelMode: "DRIVING",
        },
        (response, status) => {
            if (status !== "OK") return;

            const results = response.rows[0].elements;

            // Append distance & time to each vendor object
            vendors.forEach((vendor, index) => {
                vendor.distance_text = results[index].distance.text;
                vendor.distance_value = results[index].distance.value; // meters
                vendor.time_text = results[index].duration.text;
                vendor.time_value = results[index].duration.value; // seconds
            });

            callback(vendors); // returns vendors with distance/time added
        }
    );
}

/* ---------------------------------------------
   Show vendor markers on map
   Called when user clicks "View on Map"
--------------------------------------------- */
function showVendorMarker(vendor) {
    clearVendorMarkers();

    const marker = new google.maps.Marker({
        map: map,
        position: { lat: vendor.lat, lng: vendor.lng },
        title: vendor.name,
    });

    vendorMarkers.push(marker);

    const infoWindow = new google.maps.InfoWindow({
        content: `
            <strong>${vendor.name}</strong><br>
            Rating: ⭐ ${vendor.rating}<br>
            Distance: ${vendor.distance_text}<br>
            ETA: ${vendor.time_text}<br><br>
            <button onclick="getDirections(${vendor.lat}, ${vendor.lng})">Get Directions</button>
        `,
    });

    marker.addListener("click", () => infoWindow.open(map, marker));

    infoWindow.open(map, marker);
    map.setCenter({ lat: vendor.lat, lng: vendor.lng });
}

/* ---------------------------------------------
   Clear vendor markers
--------------------------------------------- */
function clearVendorMarkers() {
    vendorMarkers.forEach(m => m.setMap(null));
    vendorMarkers = [];
}

/* ---------------------------------------------
   Draw fastest route based on travel mode
--------------------------------------------- */
function getDirections(lat, lng, mode = "DRIVING") {
    if (!userLocation) return alert("User location missing");

    const request = {
        origin: userLocation,
        destination: { lat: lat, lng: lng },
        travelMode: mode,
    };

    directionsService.route(request, (result, status) => {
        if (status === "OK") {
            directionsRenderer.setDirections(result);
        } else {
            alert("Route not found.");
        }
    });
}

/* ---------------------------------------------
   Allow backend/frontend to switch travel mode:
   Example call: changeTravelMode("WALKING")
--------------------------------------------- */
function changeTravelMode(mode) {
    if (!directionsRenderer.getDirections()) return;
    const dest = directionsRenderer.getDirections().routes[0].legs[0].end_location;
    getDirections(dest.lat(), dest.lng(), mode);
}

/* ---------------------------------------------
   Expose functions to backend/frontend
--------------------------------------------- */
window.LocalConnectMaps = {
    computeDistanceAndTimeForVendors,
    showVendorMarker,
    changeTravelMode,
};

window.initMap = initMap; // Required by Google Maps loader
