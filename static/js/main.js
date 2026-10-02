/* КодСтарт — клиентская логика: слайдер, валидация форм, уведомления */
(function () {
  "use strict";

  // ---------- Всплывающие уведомления ----------
  function toast(message, type) {
    const box = document.getElementById("toasts");
    const el = document.createElement("div");
    el.className = "toast toast--" + (type || "success");
    el.textContent = message;
    box.appendChild(el);
    autoHide(el);
  }
  function autoHide(el) {
    setTimeout(() => { el.classList.add("hide"); setTimeout(() => el.remove(), 300); }, 3500);
  }
  document.querySelectorAll(".toast").forEach(autoHide);

  // ---------- Слайдер: 4 слайда, автопрокрутка 3 с, вперёд/назад ----------
  const slider = document.getElementById("slider");
  if (slider) {
    const slides = slider.querySelectorAll(".slider__slide");
    const bar = slider.querySelector(".slider__progress span");
    let current = 0, timer = null;

    function show(index) {
      slides[current].classList.remove("is-active");
      current = (index + slides.length) % slides.length;
      slides[current].classList.add("is-active");
      restart();
    }
    function restart() {
      clearInterval(timer);
      bar.classList.remove("run"); void bar.offsetWidth; bar.classList.add("run");
      timer = setInterval(() => show(current + 1), 3000);
    }
    slider.querySelector(".slider__btn--next").addEventListener("click", () => show(current + 1));
    slider.querySelector(".slider__btn--prev").addEventListener("click", () => show(current - 1));
    restart();
  }

  // ---------- Валидация форм регистрации/входа ----------
  const rules = {
    login: [/^[A-Za-z0-9_]{4,30}$/, "Логин: 4–30 символов, латиница, цифры, _"],
    password: [/^.{6,}$/, "Пароль — не менее 6 символов"],
    full_name: [/^[А-Яа-яЁё\- ]{5,150}$/, "ФИО — только кириллица, пробелы и дефис"],
    phone: [/^8\(\d{3}\)\d{3}-\d{2}-\d{2}$/, "Телефон в формате 8(XXX)XXX-XX-XX"],
    email: [/^[^@\s]+@[^@\s]+\.[^@\s]+$/, "Некорректный email"],
  };
  const isRegister = location.pathname.startsWith("/register");

  function setError(input, message) {
    const field = input.closest(".field");
    field.classList.toggle("has-error", !!message);
    field.classList.toggle("is-valid", !message && input.value !== "");
    const err = field.querySelector(".field__error");
    if (err) err.textContent = message || "";
  }
  function check(input) {
    if (!input.value.trim()) { setError(input, "Поле обязательно для заполнения"); return false; }
    const rule = rules[input.name];
    if (isRegister && rule && !rule[0].test(input.value.trim())) { setError(input, rule[1]); return false; }
    if (input.dataset.taken === "1") { setError(input, "Такой логин уже занят"); return false; }
    setError(input, ""); return true;
  }

  document.querySelectorAll("form[data-validate]").forEach((form) => {
    const inputs = form.querySelectorAll("input[required]");
    inputs.forEach((input) => input.addEventListener("blur", () => check(input)));
    form.addEventListener("submit", (e) => {
      const ok = [...inputs].map(check).every(Boolean);
      if (!ok) { e.preventDefault(); toast("Проверьте правильность заполнения формы", "error"); }
    });
  });

  // Проверка уникальности логина на лету
  const loginInput = document.getElementById("login");
  if (loginInput && isRegister) {
    let t;
    loginInput.addEventListener("input", () => {
      clearTimeout(t);
      t = setTimeout(async () => {
        loginInput.dataset.taken = "0";
        if (!rules.login[0].test(loginInput.value)) return;
        const r = await fetch("/api/check-login?login=" + encodeURIComponent(loginInput.value));
        const data = await r.json();
        loginInput.dataset.taken = data.available ? "0" : "1";
        setError(loginInput, data.available ? "" : "Такой логин уже занят");
      }, 400);
    });
  }

  // Маска телефона 8(XXX)XXX-XX-XX
  const phone = document.getElementById("phone");
  if (phone) {
    phone.addEventListener("input", () => {
      const d = phone.value.replace(/\D/g, "").replace(/^7/, "8").slice(0, 11);
      let v = d ? "8" : "";
      if (d.length > 1) v += "(" + d.slice(1, 4);
      if (d.length >= 4) v += ")" + d.slice(4, 7);
      if (d.length >= 7) v += "-" + d.slice(7, 9);
      if (d.length >= 9) v += "-" + d.slice(9, 11);
      phone.value = v;
    });
  }

  // ---------- Админ-панель: смена статуса без перезагрузки ----------
  document.querySelectorAll(".status-select").forEach((select) => {
    select.addEventListener("change", async () => {
      const body = new URLSearchParams({ status_id: select.value });
      const r = await fetch(select.dataset.url, { method: "POST", body });
      const data = await r.json();
      toast(data.message, data.ok ? "success" : "error");
    });
  });
})();
