(function($) {
    $(document).ready(function() {
        function toggleClubField() {
            var associationField = $('#id_association');
            var clubField = $('#id_club').closest('.form-row'); // Get the entire form-row for the club field

            if (associationField.length && clubField.length) {
                if (associationField.val()) {
                    clubField.hide();
                } else {
                    clubField.show();
                }
            }
        }

        // Initial call on page load
        toggleClubField();

        // Bind to change event of the association field
        $('#id_association').change(toggleClubField);
    });
})(django.jQuery);
