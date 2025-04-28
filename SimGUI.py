import numpy as np
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import ttk

def run_simulation(SoCi, C, Tin):
    PN = 10
    eta = 0.85
    Ts = 5 / 60
    TN = int(((1 - SoCi) * C) / (eta * PN * Ts))

    np.random.seed(0)
    k = np.arange(Tin)
    trend = 0.02 * k + 5
    seasonality = 2 * np.sin(2 * np.pi * k / 48)
    noise = np.random.normal(0, 0.5, Tin)
    price_forecast = trend + seasonality + noise

    Z = np.array([[price_forecast[i], i] for i in range(Tin)])
    Z_sorted = Z[Z[:, 0].argsort()]
    schedule_flags_sorted = np.array([1 if i < TN else 0 for i in range(Tin)])
    Z_scheduled = np.column_stack((Z_sorted, schedule_flags_sorted))
    Z_final = Z_scheduled[Z_scheduled[:, 1].argsort()]
    charging_schedule = Z_final[:, 2]

    real_price = price_forecast + np.random.normal(0, 0.3, Tin)
    execution_flags = np.zeros(Tin)
    SoC = 0
    charge_per_interval = (eta * PN * Ts) / C
    mu_rt = 0
    var_rt = 0
    gamma = lambda k: 4.5 - (4.5 / Tin) * k

    for k in range(Tin):
        mu_rt = (mu_rt * k + real_price[k]) / (k + 1)
        var_rt = ((var_rt * (k - 1) if k > 1 else 0) + (real_price[k] - mu_rt) ** 2) / (k if k > 0 else 1)
        std_rt = np.sqrt(var_rt)
        threshold = gamma(k) * std_rt
        if charging_schedule[k] == 1 and real_price[k] > mu_rt + threshold:
            execution_flags[k] = 0
        elif charging_schedule[k] == 0 and real_price[k] < mu_rt - threshold:
            execution_flags[k] = 1
        else:
            execution_flags[k] = charging_schedule[k]
        SoC += execution_flags[k] * charge_per_interval
        if SoC >= 1.0:
            break

    executed_cost = (execution_flags * real_price).sum() / execution_flags.sum()
    final_soc = SoCi + execution_flags.sum() * charge_per_interval
    soc_error = 100 * (1.0 - final_soc)

    # نمایش نتایج
    time_axis = np.arange(Tin)
    plt.figure(figsize=(12, 5))
    plt.plot(time_axis, real_price, label="قیمت واقعی", color='gray')
    plt.scatter(time_axis[execution_flags == 1], real_price[execution_flags == 1], color='blue', label="بازه‌های شارژ شده")
    plt.title(f"هزینه: ${executed_cost:.2f}/kWh | شارژ نهایی: {final_soc:.2f} | خطا: {soc_error:.2f}%")
    plt.xlabel("بازه زمانی (۵ دقیقه‌ای)")
    plt.ylabel("قیمت برق")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()

# ساخت GUI
root = tk.Tk()
root.title("شبیه‌سازی شارژ خودرو برقی (CCMS)")

tk.Label(root, text="شارژ اولیه (SoCi):").grid(row=0, column=0)
soci_entry = ttk.Entry(root)
soci_entry.insert(0, "0.5")
soci_entry.grid(row=0, column=1)

tk.Label(root, text="ظرفیت باتری (kWh):").grid(row=1, column=0)
c_entry = ttk.Entry(root)
c_entry.insert(0, "80")
c_entry.grid(row=1, column=1)

tk.Label(root, text="تعداد بازه‌های زمانی (Tin):").grid(row=2, column=0)
tin_entry = ttk.Entry(root)
tin_entry.insert(0, "132")
tin_entry.grid(row=2, column=1)

def on_run():
    SoCi = float(soci_entry.get())
    C = float(c_entry.get())
    Tin = int(tin_entry.get())
    run_simulation(SoCi, C, Tin)

run_button = ttk.Button(root, text="اجرای شبیه‌سازی", command=on_run)
run_button.grid(row=3, column=0, columnspan=2, pady=10)

root.mainloop()