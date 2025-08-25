document.addEventListener('DOMContentLoaded', function() {
    // Element selectors
    const countrySelect = document.getElementById('id_country');
    const provinceSelect = document.getElementById('id_province');
    const regionSelect = document.getElementById('id_region');
    const lfaSelect = document.getElementById('id_local_federation');
    const clubSelect = document.getElementById('id_club');

    function updateProvinces() {
        const countryId = countrySelect.value;
        provinceSelect.innerHTML = '<option value="">---------</option>';
        regionSelect.innerHTML = '<option value="">---------</option>';
        lfaSelect.innerHTML = '<option value="">---------</option>';
        clubSelect.innerHTML = '<option value="">---------</option>';

        if (countryId) {
            // This endpoint does not exist yet. I will need to create it.
            // fetch(`/api/provinces-for-country/${countryId}/`)
            //     .then(response => response.json())
            //     .then(data => {
            //         data.forEach(province => {
            //             const option = new Option(province.name, province.id);
            //             provinceSelect.add(option);
            //         });
            //     });
        }
    }

    function updateRegions() {
        const provinceId = provinceSelect.value;
        regionSelect.innerHTML = '<option value="">---------</option>';
        lfaSelect.innerHTML = '<option value="">---------</option>';
        clubSelect.innerHTML = '<option value="">---------</option>';

        if (provinceId) {
            fetch(`/api/regions-for-province/${provinceId}/`)
                .then(response => response.json())
                .then(data => {
                    data.forEach(region => {
                        const option = new Option(region.name, region.id);
                        regionSelect.add(option);
                    });
                });
        }
    }

    function updateLfas() {
        const regionId = regionSelect.value;
        lfaSelect.innerHTML = '<option value="">---------</option>';
        clubSelect.innerHTML = '<option value="">---------</option>';

        if (regionId) {
            fetch(`/api/lfas-for-region/${regionId}/`)
                .then(response => response.json())
                .then(data => {
                    data.forEach(lfa => {
                        const option = new Option(lfa.name, lfa.id);
                        lfaSelect.add(option);
                    });
                });
        }
    }

    function updateClubs() {
        const lfaId = lfaSelect.value;
        clubSelect.innerHTML = '<option value="">---------</option>';

        if (lfaId) {
            fetch(`/api/clubs-for-lfa/${lfaId}/`)
                .then(response => response.json())
                .then(data => {
                    data.forEach(club => {
                        const option = new Option(club.name, club.id);
                        clubSelect.add(option);
                    });
                });
        }
    }

    if(countrySelect) countrySelect.addEventListener('change', updateProvinces);
    if(provinceSelect) provinceSelect.addEventListener('change', updateRegions);
    if(regionSelect) regionSelect.addEventListener('change', updateLfas);
    if(lfaSelect) lfaSelect.addEventListener('change', updateClubs);
});
