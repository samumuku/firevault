// 1. Check if the page has a password field
let passwordFields = document.querySelectorAll('input[type="password"]');

if (passwordFields.length > 0) {
  let domain = window.location.hostname;

  // Ask Python server for credentials
  fetch(`http://127.0.0.1:5000/get_credentials?site=${domain}`)
    .then((response) => response.json())
    .then((data) => {
      if (data.found) {
        if (data.count === 1) {
          // Case A: Only one account - Autofill instantly
          console.log("FireVault: 1 account found. Autofilling...");
          fillForm(data.accounts[0].username, data.accounts[0].password);
        } else {
          // Case B: Multiple accounts - Show dropdown
          console.log(
            `FireVault: ${data.count} accounts found. Showing selector.`
          );
          createAccountDropdown(data.accounts);
        }
      }
    })
    .catch((err) => console.log("FireVault Connection Error", err));
}

function fillForm(username, password) {
  // Fill Password
  let passInputs = document.querySelectorAll('input[type="password"]');
  passInputs.forEach((input) => {
    input.value = password;
    input.dispatchEvent(new Event("input", { bubbles: true }));
    input.dispatchEvent(new Event("change", { bubbles: true }));
  });

  // Fill Username (Look backwards from password field)
  let inputs = Array.from(document.querySelectorAll("input"));
  let passIndex = inputs.indexOf(passInputs[0]);

  for (let i = passIndex - 1; i >= 0; i--) {
    let input = inputs[i];
    // Check if it's a text/email field and visible
    if (
      (input.type === "text" || input.type === "email") &&
      input.offsetParent !== null
    ) {
      input.value = username;
      input.dispatchEvent(new Event("input", { bubbles: true }));
      input.dispatchEvent(new Event("change", { bubbles: true }));
      return input; // Return the input field so we can attach the dropdown to it
    }
  }
  return passInputs[0]; // Fallback to password field if no user field found
}

function createAccountDropdown(accounts) {
  // 1. Find the input field to attach the dropdown to
  // We run the fill logic specifically to find the username box, but we pass empty strings initially
  let targetInput = fillForm("", "");

  // 2. Create the container div
  let container = document.createElement("div");
  container.id = "firevault-dropdown";
  container.style.position = "absolute";
  container.style.zIndex = "99999";
  container.style.backgroundColor = "#333";
  container.style.border = "1px solid #555";
  container.style.borderRadius = "5px";
  container.style.boxShadow = "0 4px 6px rgba(0,0,0,0.3)";
  container.style.fontFamily = "Arial, sans-serif";
  container.style.overflow = "hidden";

  // Position it just below the input field
  let rect = targetInput.getBoundingClientRect();
  container.style.top = window.scrollY + rect.bottom + 5 + "px";
  container.style.left = window.scrollX + rect.left + "px";
  container.style.width = Math.max(rect.width, 200) + "px"; // Match width or min 200px

  // 3. Create a header
  let header = document.createElement("div");
  header.innerText = "⚡ Select Account";
  header.style.padding = "8px 12px";
  header.style.backgroundColor = "#222";
  header.style.color = "#aaa";
  header.style.fontSize = "12px";
  header.style.fontWeight = "bold";
  header.style.borderBottom = "1px solid #444";
  container.appendChild(header);

  // 4. Create an option for each account
  accounts.forEach((acc) => {
    let option = document.createElement("div");
    option.innerText = acc.username;
    option.style.padding = "10px 12px";
    option.style.color = "white";
    option.style.fontSize = "14px";
    option.style.cursor = "pointer";
    option.style.transition = "background 0.2s";

    // Hover Effect
    option.onmouseover = () => (option.style.backgroundColor = "#2ecc71");
    option.onmouseout = () => (option.style.backgroundColor = "transparent");

    // Click Action
    option.onclick = () => {
      fillForm(acc.username, acc.password);
      container.remove(); // Close menu after selection
    };

    container.appendChild(option);
  });

  // 5. Add "Close" button at bottom (optional but good UX)
  let closeBtn = document.createElement("div");
  closeBtn.innerText = "Close";
  closeBtn.style.padding = "5px";
  closeBtn.style.textAlign = "center";
  closeBtn.style.fontSize = "10px";
  closeBtn.style.color = "#888";
  closeBtn.style.cursor = "pointer";
  closeBtn.style.borderTop = "1px solid #444";
  closeBtn.onclick = () => container.remove();
  container.appendChild(closeBtn);

  // Inject into page
  document.body.appendChild(container);
}
