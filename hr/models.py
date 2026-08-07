from django.db import models
from django.conf import settings
from academics.models import TeacherProfile
import calendar


class SalaryConfig(models.Model):
    """Global salary configuration per school — all criteria manually set."""
    school = models.OneToOneField('accounts.School', on_delete=models.CASCADE, related_name='salary_config', null=True, blank=True)
    
    # Month/Year
    month = models.PositiveIntegerField(default=1, help_text="Month (1-12)")
    year = models.PositiveIntegerField(default=2026, help_text="Year")
    
    # Basic settings
    default_working_days = models.PositiveIntegerField(default=26, help_text="Default working days per month")
    
    # Tax
    tax_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="Tax % deducted from gross")
    
    # Allowances (percentage of basic salary)
    housing_allowance_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="Housing allowance % of basic")
    medical_allowance_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="Medical allowance % of basic")
    transport_allowance_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="Transport allowance % of basic")
    fuel_allowance_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="Fuel allowance % of basic")
    
    # Bonus
    bonus_per_day = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Bonus amount per day if 0 leaves in month")
    bonus_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="Or bonus as % of basic (if per_day=0)")
    
    # Deductions
    provident_fund_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="PF % of basic")
    security_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="Security deduction % of basic")
    van_child_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="Van/Child deduction % of basic")
    max_allowed_leaves = models.PositiveIntegerField(default=0, help_text="Max paid leaves per month")
    
    # Late deduction
    late_deduction_per = models.PositiveIntegerField(default=3, help_text="Late days count as 1 half-day deduct")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Salary Config - {self.school}"

    @property
    def housing_allowance_amount(self):
        """Calculate housing allowance from first employee's salary for display."""
        return self.housing_allowance_pct
    
    def get_housing(self, basic):
        return basic * (self.housing_allowance_pct / 100)
    def get_medical(self, basic):
        return basic * (self.medical_allowance_pct / 100)
    def get_transport(self, basic):
        return basic * (self.transport_allowance_pct / 100)
    def get_fuel(self, basic):
        return basic * (self.fuel_allowance_pct / 100)
    def get_pf(self, basic):
        return basic * (self.provident_fund_pct / 100)
    def get_security(self, basic):
        return basic * (self.security_pct / 100)
    def get_van_child(self, basic):
        return basic * (self.van_child_pct / 100)
    def get_tax(self, gross):
        return gross * (self.tax_percentage / 100)
    def get_bonus(self, basic):
        if self.bonus_per_day > 0:
            return 0  # Will be calculated per day in monthly salary
        return basic * (self.bonus_percentage / 100)


class EmployeeSalary(models.Model):
    """Salary structure for each employee (teacher)."""
    SALARY_TYPE_CHOICES = (
        ('monthly', 'Monthly'),
        ('daily', 'Daily'),
    )
    EMPLOYMENT_TYPE_CHOICES = (
        ('permanent', 'Permanent'),
        ('contract', 'Contract'),
        ('daily_wager', 'Daily Wager'),
    )

    employee = models.OneToOneField(TeacherProfile, on_delete=models.CASCADE, related_name='salary_detail')
    basic_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    salary_type = models.CharField(max_length=10, choices=SALARY_TYPE_CHOICES, default='monthly')
    employment_type = models.CharField(max_length=15, choices=EMPLOYMENT_TYPE_CHOICES, default='permanent')
    working_days_per_week = models.PositiveIntegerField(default=6)
    bank_account = models.CharField(max_length=50, blank=True, default='')
    bank_name = models.CharField(max_length=100, blank=True, default='')

    # Allowances
    housing_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    medical_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    transport_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    fuel_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    other_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Per-employee salary config override (overrides global SalaryConfig when enabled)
    use_custom_config = models.BooleanField(default=False)
    custom_housing_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    custom_medical_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    custom_transport_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    custom_fuel_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    custom_tax_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    custom_pf_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    custom_security_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    custom_van_child_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    custom_bonus_per_day = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    custom_bonus_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def total_allowances(self):
        return (self.housing_allowance + self.medical_allowance +
                self.transport_allowance + self.fuel_allowance + self.other_allowance)

    def __str__(self):
        return f"{self.employee.full_name} - {self.basic_salary}"


class MonthlySalary(models.Model):
    """Monthly salary record for each employee."""
    PAY_STATUS_CHOICES = (
        ('paid', 'Paid'),
        ('unpaid', 'Unpaid'),
        ('partial', 'Partial'),
    )

    employee = models.ForeignKey(TeacherProfile, on_delete=models.CASCADE, related_name='monthly_salaries')
    salary_config = models.ForeignKey(SalaryConfig, on_delete=models.SET_NULL, null=True, blank=True)
    month = models.PositiveIntegerField()  # 1-12
    year = models.PositiveIntegerField()

    # Attendance (manually entered by HR)
    total_working_days = models.PositiveIntegerField(default=26)
    days_present = models.PositiveIntegerField(default=0)
    days_absent = models.PositiveIntegerField(default=0)
    paid_leaves = models.PositiveIntegerField(default=0, help_text="Paid leaves (no salary deduction)")
    unpaid_leaves = models.PositiveIntegerField(default=0, help_text="Unpaid leaves (salary deducted)")
    allowed_leaves = models.PositiveIntegerField(default=0, help_text="Auto-calculated from config")
    late_coming_days = models.PositiveIntegerField(default=0)

    # Month-specific salary config percentages (stored per-month for edit/update)
    cfg_housing_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    cfg_medical_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    cfg_transport_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    cfg_fuel_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    cfg_tax_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    cfg_pf_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    cfg_security_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    cfg_van_child_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    cfg_bonus_per_day = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    cfg_bonus_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    TRANSACTION_TYPE_CHOICES = (
        ('bank_islami', 'Bank Islami'),
        ('ubl', 'UBL'),
        ('cash', 'Cash in Hand'),
        ('personal', 'Personal Account'),
    )
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES, default='bank_islami')
    has_custom_config = models.BooleanField(default=False, help_text="True if per-month overrides were saved via salary config")

    # Overtime
    overtime_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0, help_text="Overtime hours this month")
    overtime_rate = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Overtime rate per hour")

    # Salary breakdown
    basic_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    increment = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    per_day_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Allowances
    housing_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    medical_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    transport_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    fuel_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    other_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Deductions
    leave_deduction = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    late_coming_deduction = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    advance_deduction = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    provident_fund = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    security_deduction = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    van_child_deduction = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_deduction = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    other_deduction = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Bonus
    bonus_per_day = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Bonus per day if no leaves taken")
    bonus_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Totals
    gross_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_deductions = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Status
    pay_status = models.CharField(max_length=10, choices=PAY_STATUS_CHOICES, default='unpaid')
    payment_date = models.DateField(null=True, blank=True)

    # Remarks
    remarks = models.TextField(blank=True, default='')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('employee', 'month', 'year')
        ordering = ['-year', '-month']

    def calculate_salary(self):
        """Auto-calculate salary based on config and attendance."""
        emp = self.employee
        emp_salary_obj = EmployeeSalary.objects.filter(employee=emp).first()

        # Get basic salary from employee profile (teacher's salary field)
        basic = float(emp.salary if emp.salary > 0 else (emp_salary_obj.basic_salary if emp_salary_obj else 0))
        self.basic_salary = basic

        # Get config — always prefer the one matching this record's month/year
        config = SalaryConfig.objects.filter(month=self.month, year=self.year).first()
        if not config:
            config = self.salary_config
        if not config:
            return

        # Check if this record has month-specific config percentages
        has_cfg = self.has_custom_config

        # Allowances — use stored percentages if set, else global config
        if has_cfg:
            self.housing_allowance = float(basic) * float(self.cfg_housing_pct) / 100
            self.medical_allowance = float(basic) * float(self.cfg_medical_pct) / 100
            self.transport_allowance = float(basic) * float(self.cfg_transport_pct) / 100
            self.fuel_allowance = float(basic) * float(self.cfg_fuel_pct) / 100
        else:
            self.housing_allowance = config.get_housing(basic)
            self.medical_allowance = config.get_medical(basic)
            self.transport_allowance = config.get_transport(basic)
            self.fuel_allowance = config.get_fuel(basic)

        # Calculate per day salary
        working = self.total_working_days if self.total_working_days > 0 else config.default_working_days
        if working > 0:
            self.per_day_salary = basic / working

        # Calculate days_present from natural calendar days - absent only (leaves don't reduce present)
        days_in_month = calendar.monthrange(self.year, self.month)[1]
        self.days_present = max(0, days_in_month - self.days_absent)

        # Set allowed leaves from config
        self.allowed_leaves = config.max_allowed_leaves

        # Leave deduction = unpaid_leaves * per_day_salary
        self.leave_deduction = self.unpaid_leaves * self.per_day_salary

        # Late coming deduction (every N lates = 1 half-day deduction)
        lates_for_deduct = self.late_coming_days // config.late_deduction_per if config.late_deduction_per > 0 else 0
        self.late_coming_deduction = lates_for_deduct * (self.per_day_salary / 2)

        # Bonus: only if 0 absent days AND 0 unpaid leaves
        if self.days_absent == 0 and self.unpaid_leaves == 0:
            if has_cfg:
                if float(self.cfg_bonus_per_day) > 0:
                    self.bonus_amount = float(self.cfg_bonus_per_day) * self.total_working_days
                else:
                    self.bonus_amount = float(basic) * float(self.cfg_bonus_pct) / 100
            else:
                if config.bonus_per_day > 0:
                    self.bonus_amount = config.bonus_per_day * self.total_working_days
                else:
                    self.bonus_amount = config.get_bonus(basic)
        else:
            self.bonus_amount = 0

        # Provident fund
        if has_cfg:
            self.provident_fund = float(basic) * float(self.cfg_pf_pct) / 100
        else:
            self.provident_fund = config.get_pf(basic)

        # Security & Van/Child
        if has_cfg:
            self.security_deduction = float(basic) * float(self.cfg_security_pct) / 100
            self.van_child_deduction = float(basic) * float(self.cfg_van_child_pct) / 100
        else:
            self.security_deduction = config.get_security(basic)
            self.van_child_deduction = config.get_van_child(basic)

        # Overtime
        overtime_pay = float(self.overtime_hours * self.overtime_rate) if self.overtime_hours > 0 and self.overtime_rate > 0 else 0

        # Gross salary
        total_allow = float(self.housing_allowance) + float(self.medical_allowance) + float(self.transport_allowance) + float(self.fuel_allowance) + float(self.other_allowance)
        self.gross_salary = (basic + float(self.increment) + total_allow + float(self.bonus_amount) + overtime_pay
                           - float(self.leave_deduction) - float(self.late_coming_deduction))

        # Tax
        if has_cfg:
            self.tax_deduction = float(self.gross_salary) * float(self.cfg_tax_pct) / 100
        else:
            self.tax_deduction = config.get_tax(self.gross_salary)

        # Total deductions
        self.total_deductions = (float(self.leave_deduction) + float(self.late_coming_deduction) +
                               float(self.advance_deduction) + float(self.provident_fund) +
                               float(self.security_deduction) + float(self.van_child_deduction) +
                               float(self.tax_deduction) + float(self.other_deduction))

        # Net salary
        self.net_salary = self.gross_salary - self.total_deductions

    def save(self, *args, **kwargs):
        try:
            self.calculate_salary()
        except Exception as e:
            import traceback
            traceback.print_exc()
        super().save(*args, **kwargs)

    @property
    def total_allowances(self):
        return (self.housing_allowance + self.medical_allowance +
                self.transport_allowance + self.fuel_allowance + self.other_allowance)

    @property
    def days_in_month(self):
        return calendar.monthrange(self.year, self.month)[1]

    @property
    def present_days(self):
        return max(0, calendar.monthrange(self.year, self.month)[1] - self.days_absent)

    def __str__(self):
        month_name = calendar.month_name[self.month]
        return f"{self.employee.full_name} - {month_name} {self.year} - {self.net_salary}"


class EmployeeAttendance(models.Model):
    """Daily attendance tracking for employees."""
    STATUS_CHOICES = (
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('leave', 'Leave'),
        ('half_day', 'Half Day'),
        ('late', 'Late'),
    )

    employee = models.ForeignKey(TeacherProfile, on_delete=models.CASCADE, related_name='employee_attendances')
    date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='present')
    check_in = models.TimeField(null=True, blank=True)
    check_out = models.TimeField(null=True, blank=True)
    remarks = models.CharField(max_length=200, blank=True, default='')

    class Meta:
        unique_together = ('employee', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"{self.employee.full_name} - {self.date} ({self.get_status_display()})"


class EmployeeDocument(models.Model):
    DOCUMENT_TYPE_CHOICES = (
        ('degree', 'Degree'),
        ('certificate', 'Certificate'),
        ('experience', 'Experience Letter'),
        ('cnic', 'CNIC'),
        ('other', 'Other'),
    )
    employee = models.ForeignKey('academics.TeacherProfile', on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPE_CHOICES)
    title = models.CharField(max_length=200, blank=True, default='')
    file = models.FileField(upload_to='employee_docs/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.employee.full_name} - {self.get_document_type_display()}: {self.title or self.file.name}"
