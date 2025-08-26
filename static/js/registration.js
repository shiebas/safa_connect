$(document).ready(function() {
    // Function to update a dropdown based on a URL
    function updateDropdown(url, dropdown, dependentDropdowns) {
        $.ajax({
            url: url,
            success: function(data) {
                dropdown.empty().append('<option value="">---------</option>');
                $.each(data, function(key, value) {
                    dropdown.append($('<option>', {
                        value: value.id,
                        text: value.name
                    }));
                });
                // Clear and disable dependent dropdowns
                $.each(dependentDropdowns, function(index, dependent) {
                    dependent.empty().append('<option value="">---------</option>').prop('disabled', true);
                });
                dropdown.prop('disabled', false);
            },
            error: function() {
                console.error("Failed to load data for dropdown.");
                dropdown.prop('disabled', true);
            }
        });
    }

    // Get the dropdown elements
    var provinceDropdown = $('#id_province');
    var regionDropdown = $('#id_region');
    var lfaDropdown = $('#id_lfa');
    var clubDropdown = $('#id_club');

    // Initially disable dependent dropdowns
    regionDropdown.prop('disabled', true);
    lfaDropdown.prop('disabled', true);
    clubDropdown.prop('disabled', true);

    // Event listener for province dropdown
    provinceDropdown.change(function() {
        var provinceId = $(this).val();
        if (provinceId) {
                        var url = '/local-accounts/api/regions-for-province/' + provinceId + '/';
            updateDropdown(url, regionDropdown, [lfaDropdown, clubDropdown]);
        } else {
            regionDropdown.empty().append('<option value="">---------</option>').prop('disabled', true);
            lfaDropdown.empty().append('<option value="">---------</option>').prop('disabled', true);
            clubDropdown.empty().append('<option value="">---------</option>').prop('disabled', true);
        }
    });

    // Event listener for region dropdown
    regionDropdown.change(function() {
        var regionId = $(this).val();
        if (regionId) {
                        var url = '/local-accounts/api/lfas-for-region/' + regionId + '/';
            updateDropdown(url, lfaDropdown, [clubDropdown]);
        } else {
            lfaDropdown.empty().append('<option value="">---------</option>').prop('disabled', true);
            clubDropdown.empty().append('<option value="">---------</option>').prop('disabled', true);
        }
    });

    // Event listener for LFA dropdown
    lfaDropdown.change(function() {
        var lfaId = $(this).val();
        if (lfaId) {
                        var url = '/local-accounts/api/clubs-for-lfa/' + lfaId + '/';
            updateDropdown(url, clubDropdown, []);
        } else {
            clubDropdown.empty().append('<option value="">---------</option>').prop('disabled', true);
        }
    });
});