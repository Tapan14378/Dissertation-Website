$(document).ready(function() {
    var fields = ['#nameField', '#emailField', '#passwordField'];
    var currentField = 0;

    function animateCar() {
        $('#car').css({left: '-200px'}).show().animate({left: '100%'}, 2500);
        setTimeout(function() {
            $(fields[currentField]).fadeIn();
            $(fields[currentField] + ' .next').fadeIn();
        }, 1300);  // Delay increased to 1.5 seconds
    }

    $('.next').on('click', function(e) {
        if (currentField == 1) {  // If it's the email field
            var email = $('#email').val();
            var emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(email)) {
                alert('Invalid email');
                return;
            }
        }

        $(fields[currentField]).fadeOut();
        $(fields[currentField] + ' .next').fadeOut(function() {
            currentField++;
            if (currentField < fields.length) {
                animateCar();
            } else {
                window.location.href = loginUrl;
            }
        });
    });

    animateCar();

    // Show password toggle
    $('#showPassword').on('click', function(){
        var passwordField = $('#password');
        var passwordFieldType = passwordField.attr('type');
        if(passwordFieldType == 'password'){
            passwordField.attr('type', 'text');
        } else {
            passwordField.attr('type', 'password');
        }
    });
});
