from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static"
)

app.secret_key = "secret123"


def get_db_connection():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


def log_activity(message):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO activity_log (message) VALUES (?)", (message,))
    conn.commit()
    conn.close()


# ---------------- HOME ----------------
@app.route("/")
def home():
    return render_template("index.html")


# ---------------- LOGIN ----------------
@app.route("/login", methods=["POST"])
def login():
    email = request.form["email"]
    password = request.form["password"]

    conn = get_db_connection()
    cursor = conn.cursor()

    # Check manager
    cursor.execute(
        "SELECT * FROM managers WHERE email = ? AND password = ?",
        (email, password)
    )
    manager = cursor.fetchone()

    if manager:
        session.clear()
        session["role"] = "manager"
        session["manager_id"] = manager["id"]
        session["name"] = manager["name"]
        session["email"] = manager["email"]
        conn.close()
        return redirect(url_for("manager_dashboard"))

    # Check employee
    cursor.execute(
        "SELECT * FROM employees WHERE email = ? AND password = ?",
        (email, password)
    )
    employee = cursor.fetchone()

    if employee:
        session.clear()
        session["role"] = "employee"
        session["employee_id"] = employee["id"]
        session["name"] = employee["name"]
        session["email"] = employee["email"]
        conn.close()
        return redirect(url_for("employee_dashboard"))

    conn.close()
    return "Invalid credentials"


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


# ---------------- MANAGER DASHBOARD ----------------
@app.route("/manager-dashboard")
def manager_dashboard():
    if session.get("role") != "manager":
        return redirect(url_for("home"))

    conn = get_db_connection()

    total_shifts = conn.execute("SELECT COUNT(*) FROM shifts").fetchone()[0]
    pending_swaps = conn.execute("SELECT COUNT(*) FROM swap_requests WHERE status = 'Pending'").fetchone()[0]
    approved_swaps = conn.execute("SELECT COUNT(*) FROM swap_requests WHERE status = 'Approved'").fetchone()[0]
    rejected_swaps = conn.execute("SELECT COUNT(*) FROM swap_requests WHERE status = 'Rejected'").fetchone()[0]

    recent_activity = conn.execute("""
        SELECT message, created_at
        FROM activity_log
        ORDER BY id DESC
        LIMIT 5
    """).fetchall()

    conn.close()

    return render_template(
        "manager-dashboard.html",
        total_shifts=total_shifts,
        pending_swaps=pending_swaps,
        approved_swaps=approved_swaps,
        rejected_swaps=rejected_swaps,
        recent_activity=recent_activity
    )


# ---------------- EMPLOYEE DASHBOARD ----------------
@app.route("/employee-dashboard")
def employee_dashboard():
    if session.get("role") != "employee":
        return redirect(url_for("home"))

    employee_id = session["employee_id"]

    conn = get_db_connection()

    shifts = conn.execute("""
        SELECT * FROM shifts
        WHERE employee_id = ?
        ORDER BY date, start_time
    """, (employee_id,)).fetchall()

    pending_swaps = conn.execute("""
        SELECT COUNT(*) FROM swap_requests
        WHERE employee_id = ? AND status = 'Pending'
    """, (employee_id,)).fetchone()[0]

    shift_count = len(shifts)

    total_hours = 0
    dates_with_shifts = set()

    for shift in shifts:
        start_h, start_m = map(int, shift["start_time"].split(":"))
        end_h, end_m = map(int, shift["end_time"].split(":"))

        start_total = start_h * 60 + start_m
        end_total = end_h * 60 + end_m

        if end_total > start_total:
            total_hours += (end_total - start_total) / 60

        dates_with_shifts.add(shift["date"])

    days_off = 7 - len(dates_with_shifts)
    if days_off < 0:
        days_off = 0

    conn.close()

    return render_template(
        "employee-dashboard.html",
        shifts=shifts,
        total_hours=int(total_hours),
        shift_count=shift_count,
        pending_swaps=pending_swaps,
        days_off=days_off
    )


# ---------------- REGISTER MANAGER ----------------
@app.route("/register-manager")
def register_manager_page():
    return render_template("register-manager.html")


@app.route("/register-manager", methods=["POST"])
def register_manager():
    name = request.form["name"]
    email = request.form["email"]
    password = request.form["password"]

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM managers WHERE email = ?", (email,))
    existing_manager = cursor.fetchone()

    if existing_manager:
        conn.close()
        return "Manager already exists."

    cursor.execute(
        "INSERT INTO managers (name, email, password) VALUES (?, ?, ?)",
        (name, email, password)
    )

    conn.commit()
    conn.close()

    return redirect(url_for("home"))


# ---------------- EMPLOYEES ----------------
@app.route("/employees")
def employees():
    if session.get("role") != "manager":
        return redirect(url_for("home"))

    conn = get_db_connection()
    employees = conn.execute("SELECT * FROM employees").fetchall()
    conn.close()

    return render_template("employees.html", employees=employees)


@app.route("/add-employee", methods=["POST"])
def add_employee():
    name = request.form["name"]
    email = request.form["email"]
    password = request.form["password"]
    role = request.form["role"]
    skill = request.form["skill"]

    conn = get_db_connection()
    cursor = conn.cursor()

    log_activity(f"New employee added: {name}")

    cursor.execute("""
        INSERT INTO employees (name, email, password, role, skill, status)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (name, email, password, role, skill, "Active"))

    conn.commit()
    conn.close()

    return redirect(url_for("employees"))


@app.route("/delete-employee/<int:id>")
def delete_employee(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM employees WHERE id = ?", (id,))

    conn.commit()
    conn.close()

    return redirect(url_for("employees"))


# ---------------- CREATE SCHEDULE ----------------
@app.route("/create-schedule")
def create_schedule():
    if session.get("role") != "manager":
        return redirect(url_for("home"))

    conn = get_db_connection()

    employees = conn.execute("SELECT * FROM employees").fetchall()

    shifts = conn.execute("""
        SELECT shifts.*, employees.name AS employee_name
        FROM shifts
        LEFT JOIN employees ON shifts.employee_id = employees.id
        ORDER BY shifts.date
    """).fetchall()

    conn.close()

    return render_template("create-schedule.html", employees=employees, shifts=shifts)


@app.route("/add-shift", methods=["POST"])
def add_shift():
    employee_id = request.form["employee_id"]
    date = request.form["date"]
    start_time = request.form["start_time"]
    end_time = request.form["end_time"]
    skill = request.form["skill"]

    conn = get_db_connection()
    cursor = conn.cursor()

    employee = conn.execute("SELECT name FROM employees WHERE id = ?", (employee_id,)).fetchone()
    employee_name = employee["name"] if employee else "Unknown Employee"

    cursor.execute("""
        INSERT INTO shifts (employee_id, date, start_time, end_time, skill)
        VALUES (?, ?, ?, ?, ?)
    """, (employee_id, date, start_time, end_time, skill))

    conn.commit()
    conn.close()

    return redirect(url_for("create_schedule"))


@app.route("/delete-shift/<int:id>")
def delete_shift(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM shifts WHERE id = ?", (id,))

    conn.commit()
    conn.close()

    return redirect(url_for("create_schedule"))


# ---------------- MANAGER SWAP REQUESTS ----------------
@app.route("/swap-requests")
def swap_requests():
    if session.get("role") != "manager":
        return redirect(url_for("home"))

    conn = get_db_connection()

    swap_requests_data = conn.execute("""
        SELECT swap_requests.*, employees.name AS employee_name,
               shifts.date, shifts.start_time, shifts.end_time, shifts.skill
        FROM swap_requests
        LEFT JOIN employees ON swap_requests.employee_id = employees.id
        LEFT JOIN shifts ON swap_requests.shift_id = shifts.id
        ORDER BY swap_requests.id DESC
    """).fetchall()

    conn.close()

    return render_template("swap-requests.html", swap_requests_data=swap_requests_data)


# ---------------- MANAGER AVAILABILITY ----------------
@app.route("/availability")
def availability():
    if session.get("role") != "manager":
        return redirect(url_for("home"))

    conn = get_db_connection()

    availability_data = conn.execute("""
        SELECT availability.*, employees.name AS employee_name
        FROM availability
        JOIN employees ON availability.employee_id = employees.id
        ORDER BY availability.day, employees.name
    """).fetchall()

    conn.close()

    return render_template("availability.html", availability_data=availability_data)


# ---------------- EMPLOYEE AVAILABILITY ----------------
@app.route("/update-availability")
def update_availability():
    if session.get("role") != "employee":
        return redirect(url_for("home"))

    employee_id = session["employee_id"]

    conn = get_db_connection()
    availability = conn.execute("""
        SELECT * FROM availability
        WHERE employee_id = ?
        ORDER BY id DESC
    """, (employee_id,)).fetchall()
    conn.close()

    return render_template("update-availability.html", availability=availability)


@app.route("/save-availability", methods=["POST"])
def save_availability():
    if session.get("role") != "employee":
        return redirect(url_for("home"))

    employee_id = session["employee_id"]
    day = request.form["day"]
    from_time = request.form["from_time"]
    to_time = request.form["to_time"]

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO availability (employee_id, day, from_time, to_time, status)
        VALUES (?, ?, ?, ?, ?)
    """, (employee_id, day, from_time, to_time, "Available"))

    conn.commit()
    conn.close()

    employee_name = session.get("name", "Employee")
    log_activity(f"{employee_name} updated availability for {day} ({from_time} - {to_time})")

    return redirect(url_for("update_availability"))


# ---------------- EMPLOYEE SWAP REQUESTS ----------------
@app.route("/request-swap")
def request_swap():
    if session.get("role") != "employee":
        return redirect(url_for("home"))

    employee_id = session["employee_id"]

    conn = get_db_connection()

    shifts = conn.execute("""
        SELECT * FROM shifts
        WHERE employee_id = ?
        ORDER BY date, start_time
    """, (employee_id,)).fetchall()

    employees = conn.execute("""
        SELECT * FROM employees
        WHERE id != ?
        ORDER BY name
    """, (employee_id,)).fetchall()

    swap_history = conn.execute("""
        SELECT swap_requests.*, shifts.date, shifts.start_time, shifts.end_time, shifts.skill
        FROM swap_requests
        LEFT JOIN shifts ON swap_requests.shift_id = shifts.id
        WHERE swap_requests.employee_id = ?
        ORDER BY swap_requests.id DESC
    """, (employee_id,)).fetchall()

    conn.close()

    return render_template(
        "request-swap.html",
        shifts=shifts,
        employees=employees,
        swap_history=swap_history
    )


@app.route("/submit-swap-request", methods=["POST"])
def submit_swap_request():
    if session.get("role") != "employee":
        return redirect(url_for("home"))

    employee_id = session["employee_id"]
    shift_id = request.form["shift_id"]
    replacement_employee = request.form["replacement_employee"]
    reason = request.form["reason"]

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO swap_requests (employee_id, shift_id, replacement_employee, reason, status)
        VALUES (?, ?, ?, ?, ?)
    """, (employee_id, shift_id, replacement_employee, reason, "Pending"))

    conn.commit()
    conn.close()

    employee_name = session.get("name", "Employee")
    log_activity(f"{employee_name} submitted a swap request")

    return redirect(url_for("request_swap"))

@app.route("/approve-swap/<int:id>")
def approve_swap(id):
    if session.get("role") != "manager":
        return redirect(url_for("home"))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE swap_requests
        SET status = 'Approved'
        WHERE id = ?
    """, (id,))

    conn.commit()
    conn.close()

    log_activity(f"Swap request #{id} approved")

    return redirect(url_for("swap_requests"))


@app.route("/reject-swap/<int:id>")
def reject_swap(id):
    if session.get("role") != "manager":
        return redirect(url_for("home"))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE swap_requests
        SET status = 'Rejected'
        WHERE id = ?
    """, (id,))

    conn.commit()
    conn.close()

    log_activity(f"Swap request #{id} rejected")

    return redirect(url_for("swap_requests"))


@app.route("/edit-employee/<int:id>", methods=["GET", "POST"])
def edit_employee(id):
    if session.get("role") != "manager":
        return redirect(url_for("home"))

    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        role = request.form["role"]
        skill = request.form["skill"]
        status = request.form["status"]

        cursor.execute("""
            UPDATE employees
            SET name = ?, email = ?, password = ?, role = ?, skill = ?, status = ?
            WHERE id = ?
        """, (name, email, password, role, skill, status, id))

        conn.commit()
        conn.close()

        log_activity(f"Employee updated: {name}")

        return redirect(url_for("employees"))

    employee = cursor.execute("SELECT * FROM employees WHERE id = ?", (id,)).fetchone()
    conn.close()

    return render_template("edit-employee.html", employee=employee)

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)