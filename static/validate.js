// Browser-side checks. The server repeats the same rules.
function showErrors(errors) {
  var list = document.getElementById("errors");
  list.innerHTML = "";
  errors.forEach(function (msg) {
    var li = document.createElement("li");
    li.textContent = msg;
    list.appendChild(li);
  });
}

function value(form, field) {
  return form.elements[field].value;
}

var registerForm = document.getElementById("register-form");
if (registerForm) {
  registerForm.addEventListener("submit", function (e) {
    var errors = [];
    var password = value(registerForm, "password");
    var confirm = value(registerForm, "confirm_password");

    if (!value(registerForm, "name").trim()) errors.push("Name is required");
    if (!value(registerForm, "email").trim()) errors.push("Email is required");
    if (!password) errors.push("Password is required");
    if (!confirm) errors.push("Confirm password is required");
    else if (password && confirm !== password) errors.push("Passwords do not match");

    if (errors.length) {
      e.preventDefault();
      showErrors(errors);
    }
  });
}

var loginForm = document.getElementById("login-form");
if (loginForm) {
  loginForm.addEventListener("submit", function (e) {
    var errors = [];
    if (!value(loginForm, "email").trim()) errors.push("Email is required");
    if (!value(loginForm, "password")) errors.push("Password is required");

    if (errors.length) {
      e.preventDefault();
      showErrors(errors);
    }
  });
}
