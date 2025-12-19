document.addEventListener("DOMContentLoaded", () => {
  const container     = document.querySelector(".container");
  const signUpBtn     = document.querySelector("#sign-up-btn");
  const signInBtn     = document.querySelector("#sign-in-btn");
  const loginForm     = document.querySelector("#login-form");
  const registerForm  = document.querySelector("#register-form");

  // =======================
  // PANEL + FORM TOGGLE
  // =======================

  function showLogin() {
    if (!container || !loginForm || !registerForm) return;
    container.classList.remove("sign-up-mode");
    loginForm.classList.add("active");
    registerForm.classList.remove("active");
  }

  function showRegister() {
    if (!container || !loginForm || !registerForm) return;
    container.classList.add("sign-up-mode");
    registerForm.classList.add("active");
    loginForm.classList.remove("active");
  }

  if (signUpBtn) {
    signUpBtn.addEventListener("click", showRegister);
  }

  if (signInBtn) {
    signInBtn.addEventListener("click", showLogin);
  }

  // =======================
  // VALIDATION HELPERS
  // =======================

  function setFieldError(group, message) {
    if (!group) return;

    group.classList.add("has-error");

    let errorEl = group.querySelector(".field-error");
    if (!errorEl) {
      errorEl = document.createElement("p");
      errorEl.classList.add("field-error");
      group.appendChild(errorEl);
    }
    errorEl.textContent = message;
  }

  function clearFieldError(group) {
    if (!group) return;
    group.classList.remove("has-error");
    const errorEl = group.querySelector(".field-error");
    if (errorEl) errorEl.textContent = "";
  }

  function clearAllErrors(form) {
    const groups = form.querySelectorAll(".input-group");
    groups.forEach(clearFieldError);
  }

  // =======================
  // LOGIN VALIDATION
  // =======================

  if (loginForm) {
    loginForm.addEventListener("submit", (e) => {
      e.preventDefault();

      const usernameGroup = loginForm.querySelector("input[name='username']")?.closest(".input-group");
      const passwordGroup = loginForm.querySelector("input[name='password']")?.closest(".input-group");

      const username = usernameGroup?.querySelector("input")?.value.trim() || "";
      const password = passwordGroup?.querySelector("input")?.value.trim() || "";

      let valid = true;
      clearAllErrors(loginForm);

      if (!username) {
        setFieldError(usernameGroup, "Please enter your username.");
        valid = false;
      }

      if (!password) {
        setFieldError(passwordGroup, "Please enter your password.");
        valid = false;
      }

      if (valid) {
        loginForm.submit();  // send to /login
      }
    });
  }

  // =======================
  // REGISTER VALIDATION
  // =======================

  if (registerForm) {
    registerForm.addEventListener("submit", (e) => {
      e.preventDefault();

      const usernameGroup = registerForm.querySelector("input[name='username']")?.closest(".input-group");
      const emailGroup    = registerForm.querySelector("input[name='email']")?.closest(".input-group");
      const passwordGroup = registerForm.querySelector("input[name='password']")?.closest(".input-group");
      const confirmGroup  = registerForm.querySelector("input[name='confirm']")?.closest(".input-group");

      const username = usernameGroup?.querySelector("input")?.value.trim() || "";
      const email    = emailGroup?.querySelector("input")?.value.trim() || "";
      const password = passwordGroup?.querySelector("input")?.value.trim() || "";
      const confirm  = confirmGroup?.querySelector("input")?.value.trim() || "";

      let valid = true;
      clearAllErrors(registerForm);

      if (!username) {
        setFieldError(usernameGroup, "Please choose a username.");
        valid = false;
      }

      if (!password) {
        setFieldError(passwordGroup, "Please create a password.");
        valid = false;
      } else if (password.length < 6) {
        setFieldError(passwordGroup, "Password should be at least 6 characters.");
        valid = false;
      }

      if (!confirm) {
        setFieldError(confirmGroup, "Please confirm your password.");
        valid = false;
      } else if (password && confirm && password !== confirm) {
        setFieldError(confirmGroup, "Passwords do not match.");
        valid = false;
      }

      if (valid) {
        registerForm.submit();  // send to /register
      }
    });
  }
});

/// =======================////
/// PROFILE ERROR MESSAGES ////
///=======================////


window.addEventListener("DOMContentLoaded", () => {
    const box = document.getElementById("profile-message");
    if (!box) return;

    const hasSuccess = box.dataset.success && box.dataset.success.trim() !== "";
    const hasError = box.dataset.error && box.dataset.error.trim() !== "";

    if (!hasSuccess && !hasError) {
        return;
    }

    // already visible via .show class in HTML
    setTimeout(() => {
        box.classList.remove("show");
        setTimeout(() => {
            box.classList.add("hidden");
        }, 250);
    }, 4000);
});

/// ==================////
/// Add transactions toggle + warning message //////
/// ======================///

// ===== ADD TRANSACTION PAGE LOGIC =====

document.addEventListener("DOMContentLoaded", () => {
    const expenseBtn  = document.getElementById("expenseBtn");
    const incomeBtn   = document.getElementById("incomeBtn");
    const savingsBtn  = document.getElementById("savingsBtn");
    const savingswithdrawnBtn = document.getElementById("savingswithdrawnBtn")

    const expenseForm = document.getElementById("expenseForm");
    const incomeForm  = document.getElementById("incomeForm");
    const savingsForm = document.getElementById("savingsForm");
    const savingswithdrawnForm = document.getElementById("savingswithdrawnForm")

    if (!expenseBtn || !incomeBtn || !savingsBtn) {
        // Not on add.html, skip
        return;
    }

    function showForm(type) {
        // Buttons
        [expenseBtn, incomeBtn, savingsBtn,savingswithdrawnBtn].forEach(btn =>
            btn.classList.remove("active")
        );

        // Forms
        [expenseForm, incomeForm, savingsForm,savingswithdrawnForm].forEach(form =>
            form.classList.add("hidden")
        );

        if (type === "expense") {
            expenseBtn.classList.add("active");
            expenseForm.classList.remove("hidden");
        } else if (type === "income") {
            incomeBtn.classList.add("active");
            incomeForm.classList.remove("hidden");
        } else if (type === "savings") {
            savingsBtn.classList.add("active");
            savingsForm.classList.remove("hidden");
        } else if (type === "savingswithdrawn") {
          savingswithdrawnBtn.classList.add("active");
          savingswithdrawnForm.classList.remove("hidden");
        }
    }

    expenseBtn.addEventListener("click", () => showForm("expense"));
    incomeBtn.addEventListener("click", () => showForm("income"));
    savingsBtn.addEventListener("click", () => showForm("savings"));
    savingswithdrawnBtn.addEventListener("click", () => showForm("savingswithdrawn"));

    // ===== Unsaved changes protection =====

    let isDirty = false;

    const allForms = [expenseForm, incomeForm, savingsForm];

    allForms.forEach(form => {
        if (!form) return;
        form.querySelectorAll("input, select, textarea").forEach(el => {
            el.addEventListener("input", () => {
                isDirty = true;
            });
        });

        form.addEventListener("submit", () => {
            isDirty = false; // user is saving, no need to warn
        });
    });

    window.addEventListener("beforeunload", (e) => {
        if (!isDirty) return;
        e.preventDefault();
        e.returnValue = ""; // required for Chrome
    });
});


document.addEventListener("DOMContentLoaded", () => {
  const alertBox = document.querySelector(".alert");
  if (alertBox) {
    setTimeout(() => {
      alertBox.classList.add("fade-out");
    }, 3000);
  }
});
