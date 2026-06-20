function goToManager() {
  window.location.href = "manager-dashboard.html";
}

function goToEmployee() {
  window.location.href = "employee-dashboard.html";
}

// =========================
// CREATE SCHEDULE
// =========================
function addShiftRow() {
  const tableBody = document.getElementById("scheduleTableBody");
  if (!tableBody) return;

  const newRow = document.createElement("tr");
  newRow.innerHTML = `
    <td>Thu, Feb 27</td>
    <td><input type="time" value="09:00" /></td>
    <td><input type="time" value="17:00" /></td>
    <td>
      <select>
        <option>Cashier</option>
        <option>Floor Staff</option>
        <option>Stock Room</option>
      </select>
    </td>
    <td>
      <select class="employee-select"></select>
    </td>
    <td><button class="delete-btn" onclick="deleteRow(this)">Delete</button></td>
  `;

  tableBody.appendChild(newRow);
  populateEmployeeDropdowns();
}

function deleteRow(button) {
  const row = button.parentElement.parentElement;
  row.remove();
}

function publishSchedule() {
  const rows = document.querySelectorAll("#scheduleTableBody tr");
  let shifts = [];

  rows.forEach(row => {
    const date = row.children[0].innerText;
    const start = row.children[1].querySelector("input").value;
    const end = row.children[2].querySelector("input").value;
    const skill = row.children[3].querySelector("select").value;
    const employee = row.children[4].querySelector("select").value;

    shifts.push({
      date,
      start,
      end,
      skill,
      employee
    });
  });

  localStorage.setItem("shifts", JSON.stringify(shifts));

  alert("Schedule published successfully!");

  updateDashboardCounts();
}

// =========================
// OLD STATIC SWAP ACTIONS
// kept for safety if any old page still calls these
// =========================
function approveRequest(button) {
  const row = button.parentElement.parentElement;
  const statusCell = row.children[4];
  const actionCell = row.children[5];

  statusCell.innerHTML = '<span class="status approved">Approved</span>';
  actionCell.innerHTML = "Approved";
}

function rejectRequest(button) {
  const row = button.parentElement.parentElement;
  const statusCell = row.children[4];
  const actionCell = row.children[5];

  statusCell.innerHTML = '<span class="status rejected">Rejected</span>';
  actionCell.innerHTML = "Rejected";
}

// =========================
// EMPLOYEES
// =========================
function getEmployees() {
  return JSON.parse(localStorage.getItem("employees")) || [
    {
      name: "John Smith",
      contact: "john.smith@company.com",
      role: "Full-Time",
      skill: "Cashier",
      status: "Active"
    },
    {
      name: "Sarah Johnson",
      contact: "sarah.johnson@company.com",
      role: "Part-Time",
      skill: "Floor Staff",
      status: "Active"
    },
    {
      name: "Mike Davis",
      contact: "mike.davis@company.com",
      role: "Full-Time",
      skill: "Stock Room",
      status: "Active"
    }
  ];
}

function saveEmployees(employees) {
  localStorage.setItem("employees", JSON.stringify(employees));
}

function loadEmployees() {
  const tableBody = document.getElementById("employeeTableBody");
  if (!tableBody) return;

  const employees = getEmployees();
  tableBody.innerHTML = "";

  employees.forEach((emp, index) => {
    const statusClass = emp.status === "Active" ? "approved" : "pending";

    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${emp.name}</td>
      <td>${emp.contact}</td>
      <td>${emp.role}</td>
      <td>${emp.skill}</td>
      <td><span class="status ${statusClass}">${emp.status}</span></td>
      <td><button class="delete-btn" onclick="deleteEmployee(${index})">Delete</button></td>
    `;
    tableBody.appendChild(row);
  });
}

function addEmployee() {
  const name = prompt("Enter employee name:");
  if (!name) return;

  const contact = prompt("Enter employee email/contact:");
  if (!contact) return;

  const role = prompt("Enter role (Full-Time / Part-Time):");
  if (!role) return;

  const skill = prompt("Enter skill (Cashier / Floor Staff / Stock Room):");
  if (!skill) return;

  const status = prompt("Enter status (Active / Inactive):", "Active") || "Active";

  const employees = getEmployees();

  employees.push({
    name,
    contact,
    role,
    skill,
    status
  });

  saveEmployees(employees);
  loadEmployees();
}

function deleteEmployee(index) {
  const employees = getEmployees();
  employees.splice(index, 1);
  saveEmployees(employees);
  loadEmployees();
}

function searchEmployee() {
  const input = document.getElementById("searchEmployee");
  if (!input) return;

  const filter = input.value.toLowerCase();
  const rows = document.querySelectorAll("#employeeTableBody tr");

  rows.forEach((row) => {
    const name = row.children[0].innerText.toLowerCase();
    const contact = row.children[1].innerText.toLowerCase();
    const skill = row.children[3].innerText.toLowerCase();

    if (
      name.includes(filter) ||
      contact.includes(filter) ||
      skill.includes(filter)
    ) {
      row.style.display = "";
    } else {
      row.style.display = "none";
    }
  });
}

// =========================
// EMPLOYEE AVAILABILITY
// =========================
function saveAvailability() {
  const day = document.getElementById("day").value;
  const from = document.getElementById("fromTime").value;
  const to = document.getElementById("toTime").value;

  if (!from || !to) {
    alert("Please fill time");
    return;
  }

  const table = document.getElementById("availabilityTable");
  if (!table) return;

  const newRow = document.createElement("tr");
  newRow.innerHTML = `
    <td>${day}</td>
    <td>${from}</td>
    <td>${to}</td>
    <td><span class="status approved">Available</span></td>
  `;

  table.appendChild(newRow);
}

// =========================
// SWAP REQUESTS - EMPLOYEE SIDE
// =========================
function submitSwapRequest() {
  const shift = document.getElementById("swapShift").value;
  const replacement = document.getElementById("replacementEmployee").value;
  const reason = document.getElementById("swapReason").value;

  if (!reason) {
    alert("Please enter a reason for swap.");
    return;
  }

  const newRequest = {
    shift: shift,
    replacement: replacement,
    reason: reason,
    status: "Pending"
  };

  let requests = JSON.parse(localStorage.getItem("swapRequests")) || [];
  requests.push(newRequest);
  localStorage.setItem("swapRequests", JSON.stringify(requests));

  alert("Swap request submitted!");

  document.getElementById("swapReason").value = "";

  loadSwapRequests();
}

function loadSwapRequests() {
  const table = document.getElementById("swapRequestTable");
  if (!table) return;

  table.innerHTML = "";

  let requests = JSON.parse(localStorage.getItem("swapRequests")) || [];

  requests.forEach((req) => {
    const statusClass =
      req.status === "Approved"
        ? "approved"
        : req.status === "Rejected"
        ? "rejected"
        : "pending";

    const row = document.createElement("tr");

    row.innerHTML = `
      <td>${req.shift}</td>
      <td>${req.replacement}</td>
      <td>${req.reason}</td>
      <td><span class="status ${statusClass}">${req.status}</span></td>
    `;

    table.appendChild(row);
  });
}

// =========================
// SWAP REQUESTS - MANAGER SIDE
// =========================
function loadManagerSwapRequests() {
  const table = document.getElementById("managerSwapTable");
  if (!table) return;

  table.innerHTML = "";

  let requests = JSON.parse(localStorage.getItem("swapRequests")) || [];

  requests.forEach((req, index) => {
    const statusClass =
      req.status === "Approved"
        ? "approved"
        : req.status === "Rejected"
        ? "rejected"
        : "pending";

    const row = document.createElement("tr");

    row.innerHTML = `
      <td>John Smith</td>
      <td>${req.shift}</td>
      <td>${req.replacement}</td>
      <td>${req.reason}</td>
      <td><span class="status ${statusClass}">${req.status}</span></td>
      <td>
        ${
          req.status === "Pending"
            ? `
              <button class="approve-btn" onclick="approveStoredRequest(${index})">Approve</button>
              <button class="reject-btn" onclick="rejectStoredRequest(${index})">Reject</button>
            `
            : req.status
        }
      </td>
    `;

    table.appendChild(row);
  });
}

function approveStoredRequest(index) {
  let requests = JSON.parse(localStorage.getItem("swapRequests")) || [];
  requests[index].status = "Approved";
  localStorage.setItem("swapRequests", JSON.stringify(requests));
  loadManagerSwapRequests();
  loadSwapRequests();
  updateDashboardCounts();
}

function rejectStoredRequest(index) {
  let requests = JSON.parse(localStorage.getItem("swapRequests")) || [];
  requests[index].status = "Rejected";
  localStorage.setItem("swapRequests", JSON.stringify(requests));
  loadManagerSwapRequests();
  loadSwapRequests();
  updateDashboardCounts();
}

// =========================
// PAGE LOAD
// =========================
function populateEmployeeDropdowns() {
  const employeeSelects = document.querySelectorAll(".employee-select");
  if (!employeeSelects.length) return;

  const employees = getEmployees();

  employeeSelects.forEach((select) => {
    const currentValue = select.value;
    select.innerHTML = "";

    employees.forEach((emp) => {
      const option = document.createElement("option");
      option.value = emp.name;
      option.textContent = emp.name;
      select.appendChild(option);
    });

    if (currentValue) {
      select.value = currentValue;
    }
  });
}
function updateDashboardCounts() {
  const totalShiftsEl = document.getElementById("totalShiftsCount");
  const pendingEl = document.getElementById("pendingSwapsCount");
  const approvedEl = document.getElementById("approvedSwapsCount");
  const rejectedEl = document.getElementById("rejectedSwapsCount");

  // If dashboard elements not found, stop
  if (!totalShiftsEl && !pendingEl && !approvedEl && !rejectedEl) return;

  // =========================
  // SWAP REQUEST COUNTS
  // =========================
  const requests = JSON.parse(localStorage.getItem("swapRequests")) || [];

  const pendingCount = requests.filter(req => req.status === "Pending").length;
  const approvedCount = requests.filter(req => req.status === "Approved").length;
  const rejectedCount = requests.filter(req => req.status === "Rejected").length;

  // =========================
  // TOTAL SHIFTS (REAL NOW)
  // =========================
  const savedShifts = JSON.parse(localStorage.getItem("shifts")) || [];
  const totalShifts = savedShifts.length;

  // =========================
  // UPDATE UI
  // =========================
  if (totalShiftsEl) totalShiftsEl.textContent = totalShifts;
  if (pendingEl) pendingEl.textContent = pendingCount;
  if (approvedEl) approvedEl.textContent = approvedCount;
  if (rejectedEl) rejectedEl.textContent = rejectedCount;
}
function renderEmployeeSchedule() {
  const weekGrid = document.getElementById("employeeWeekGrid");
  const totalHoursEl = document.getElementById("employeeTotalHours");
  const shiftCountEl = document.getElementById("employeeShiftCount");
  const pendingSwapsEl = document.getElementById("employeePendingSwaps");
  const daysOffEl = document.getElementById("employeeDaysOff");

  if (!weekGrid) return;

  const employeeName = "John Smith";
  const allShifts = JSON.parse(localStorage.getItem("shifts")) || [];
  const allRequests = JSON.parse(localStorage.getItem("swapRequests")) || [];

  const employeeShifts = allShifts.filter(shift => shift.employee === employeeName);

  const days = [
    { short: "MON", full: "Mon" },
    { short: "TUE", full: "Tue" },
    { short: "WED", full: "Wed" },
    { short: "THU", full: "Thu" },
    { short: "FRI", full: "Fri" },
    { short: "SAT", full: "Sat" },
    { short: "SUN", full: "Sun" }
  ];

  weekGrid.innerHTML = "";

  let totalHours = 0;
  let workedDays = 0;

  days.forEach(day => {
    const shift = employeeShifts.find(s => s.date.startsWith(day.full));

    const card = document.createElement("div");

    if (shift) {
      workedDays++;

      const startHour = parseInt(shift.start.split(":")[0], 10);
      const endHour = parseInt(shift.end.split(":")[0], 10);
      const duration = endHour - startHour;
      totalHours += duration;

      card.className = "day-card";
      card.innerHTML = `
        <h3>${day.short}</h3>
        <p>${shift.start} - ${shift.end}</p>
        <span>${shift.skill}</span>
      `;
    } else {
      card.className = "day-card off-day";
      card.innerHTML = `
        <h3>${day.short}</h3>
        <p>Day Off</p>
      `;
    }

    weekGrid.appendChild(card);
  });

  const pendingSwaps = allRequests.filter(req => req.status === "Pending").length;
  const daysOff = 7 - workedDays;

  if (totalHoursEl) totalHoursEl.textContent = totalHours;
  if (shiftCountEl) shiftCountEl.textContent = employeeShifts.length;
  if (pendingSwapsEl) pendingSwapsEl.textContent = pendingSwaps;
  if (daysOffEl) daysOffEl.textContent = daysOff;
}

window.onload = function () {
  loadSwapRequests();
  loadManagerSwapRequests();
  loadEmployees();
  populateEmployeeDropdowns();
  loadSavedShifts();
  updateDashboardCounts();
  renderEmployeeSchedule();
};