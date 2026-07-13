

document.addEventListener("DOMContentLoaded", function(){

    document.querySelectorAll("form").forEach(function(form){

        form.addEventListener("submit", function(){

            document.getElementById(
                "loader-overlay"
            ).style.display = "block";

        });

    });

});

document.addEventListener(
'DOMContentLoaded',
 
function () {
 
    var calendar = new FullCalendar.Calendar(
        document.getElementById('calendar'),
 
        {
            initialView: 'dayGridMonth',
            events: '/calendar/events/'
        }
    );
 
    calendar.render();
});
