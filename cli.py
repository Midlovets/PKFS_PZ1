import logging
from electricity_billing import ElectricityBillingSystem


def run_cli():
    """Запуск командного інтерфейсу для системи обліку електроенергії."""
    billing_system = ElectricityBillingSystem()
    
    try:
        while True:
            print("\n" + "=" * 40)
            print("    СИСТЕМА ОБЛІКУ ЕЛЕКТРОЕНЕРГІЇ")
            print("=" * 40)
            print("1. Додати новий лічильник")
            print("2. Ввести показники лічильника")
            print("3. Переглянути історію лічильника")
            print("4. Переглянути всі лічильники")
            print("5. Вихід")
            print("-" * 40)

            choice = input("Виберіть опцію (1-5): ")

            if choice == "1":
                meter_id = input("\nВведіть ID нового лічильника: ").strip()

                if billing_system.meters_collection.find_one({"meter_id": meter_id}):
                    print(f"Помилка: Лічильник з ID {meter_id} вже існує.")
                    continue

                try:
                    day_reading = float(input("Введіть перші денні показники: "))
                    night_reading = float(input("Введіть перші нічні показники: "))

                    billing_system.add_new_meter(meter_id, day_reading, night_reading)
                    print(f"\nЛічильник {meter_id} успішно додано!")

                except ValueError:
                    print("Помилка: Введено некоректне значення. Спробуйте ще раз.")

            elif choice == "2":
                meter_id = input("\nВведіть ID лічильника: ").strip()

                existing_meter = billing_system.meters_collection.find_one({"meter_id": meter_id})
                if not existing_meter:
                    print(f"Помилка: Лічильник з ID {meter_id} не знайдено.")
                    continue

                try:
                    day_reading = float(input("Введіть денні показники: "))
                    night_reading = float(input("Введіть нічні показники: "))

                    if day_reading < existing_meter['day_reading']:
                        print(f"Помилка: Денний показник {day_reading} менший за попередній ({existing_meter['day_reading']}).")
                        continue

                    if night_reading < existing_meter['night_reading']:
                        print(f"Помилка: Нічний показник {night_reading} менший за попередній ({existing_meter['night_reading']}).")
                        continue

                    result = billing_system.update_meter_readings(meter_id, day_reading, night_reading)

                    print("\n" + "-" * 40)
                    print("             ДЕТАЛІ РАХУНКУ")
                    print("-" * 40)
                    print(f"ID лічильника: {result['meter_id']}")
                    print(f"Дата: {result['date']}")
                    print(f"Споживання день: {result['day_consumption']} кВт·год (тариф: {result['day_tariff']} грн/кВт·год)")
                    print(f"Споживання ніч: {result['night_consumption']} кВт·год (тариф: {result['night_tariff']} грн/кВт·год)")
                    print(f"Загальна сума: {result['total_amount']} грн")
                    print("-" * 40)

                except ValueError:
                    print("Помилка: Введено некоректне значення. Спробуйте ще раз.")

            elif choice == "3":
                meter_id = input("\nВведіть ID лічильника: ").strip()
                history = billing_system.get_meter_history(meter_id)

                if not history:
                    print(f"Історія для лічильника з ID {meter_id} не знайдена.")
                    continue

                print(f"\n----- ІСТОРІЯ ЛІЧИЛЬНИКА {meter_id} -----")
                for i, record in enumerate(history):
                    print(f"\nЗапис {i+1}:")
                    print(f"Дата: {record['date']}")
                    print(f"Денні показники: {record['current_day_reading']} кВт·год")
                    print(f"Нічні показники: {record['current_night_reading']} кВт·год")
                    print(f"Споживання день: {record['day_consumption']} кВт·год")
                    print(f"Споживання ніч: {record['night_consumption']} кВт·год")
                    print(f"Сума: {record['total_amount']} грн")
                    print("-" * 40)

            elif choice == "4":
                meters = billing_system.get_all_meters()

                if not meters:
                    print("\nУ системі немає зареєстрованих лічильників.")
                    continue

                print("\n" + "-" * 40)
                print("           ВСІ ЛІЧИЛЬНИКИ")
                print("-" * 40)
                for meter in meters:
                    print(f"\nID лічильника: {meter['meter_id']}")
                    print(f"Поточні денні показники: {meter['day_reading']} кВт·год")
                    print(f"Поточні нічні показники: {meter['night_reading']} кВт·год")
                    print(f"Останнє оновлення: {meter['date']}")
                    print("-" * 40)

            elif choice == "5":
                print("\nВихід із системи. До побачення!")
                break

            else:
                print("Помилка: Некоректний вибір. Спробуйте ще раз.")

    finally:
        billing_system.close()
