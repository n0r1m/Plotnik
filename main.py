import re
import numpy as np
import matplotlib.pyplot as plt
from aiogram import Bot, Dispatcher, types
from aiogram.types import FSInputFile
from aiogram.fsm.storage.memory import MemoryStorage
import asyncio
from matplotlib.patches import Rectangle

# Токен вашего бота
TOKEN = ''

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Функция для парсинга сообщения и извлечения данных
def parse_message(text):
    # Проверка, есть ли в конце сообщение слово "сетка"
    has_grid = "сетка" in text.strip()

    # Проверка на погрешности
    error_match = re.search(r'погрешность\(([\d.]+),([\d.]+)\)', text)
    if error_match:
        xd, yd = float(error_match.group(1)), float(error_match.group(2))
        text = re.sub(r'погрешность\([\d.]+,[\d.]+\)', '', text).strip()  # Убираем погрешность из текста
    else:
        xd, yd = None, None
    
    # Убираем слово "сетка", если оно есть, для парсинга остальных данных
    if has_grid:
        text = text.replace("сетка", "").strip()  # Убираем слово "сетка" с конца
    
    # Регулярное выражение для извлечения данных
    pattern = r'чертила "(.*?)" \{(.*?),(.*?)\} \[(.*?)\]'
    match = re.match(pattern, text)
    
    if not match:
        return None

    # Извлечение названия графика, названий осей и точек
    graph_title = match.group(1).strip()
    x_label = match.group(2).strip()
    y_label = match.group(3).strip()
    
    # Извлечение и преобразование точек
    points_str = match.group(4).strip()
    points = [tuple(map(float, point.split(','))) for point in points_str.split()]

    return graph_title, x_label, y_label, points, has_grid, xd, yd

# Функция для построения графика на основе данных
def build_graph(title, x_label, y_label, points, has_grid, xd, yd):
    # Разбиваем точки на X и Y координаты
    x_data, y_data = zip(*points)
    
    # Находим коэффициенты линейной регрессии (y = a * x + b)
    a, b = np.polyfit(x_data, y_data, 1)

    # Генерация данных для прямой линии
    x_line = np.linspace(min(x_data), max(x_data), 100)
    y_line = a * x_line + b
    
    # Построение графика
    plt.figure()
    ax = plt.gca()
    plt.scatter(x_data, y_data, color='red')
    plt.plot(x_line, y_line, color='blue')

    # Добавление прямоугольников погрешности, если параметры xd и yd заданы
    if xd is not None and yd is not None:
        for (x, y) in points:
            rect = Rectangle((x - xd, y - yd), 2 * xd, 2 * yd, linewidth=1, edgecolor='green', facecolor='none')
            ax.add_patch(rect)

    plt.title(title)
    plt.xlabel(x_label)
    plt.ylabel(y_label)

    # Включение сетки, если параметр has_grid = True
    if has_grid:
        plt.grid(True)

    # Сохранение графика в файл
    plt.savefig('linear_plot.png')
    plt.close()

# Хендлер для обработки сообщений
@dp.message()
async def send_custom_plot(message: types.Message):
    # Парсим сообщение
    parsed_data = parse_message(message.text)
    
    if parsed_data:
        title, x_label, y_label, points, has_grid, xd, yd = parsed_data

        # Строим график
        build_graph(title, x_label, y_label, points, has_grid, xd, yd)
        
        # Отправляем изображение
        plot_file = FSInputFile('linear_plot.png')
        await message.answer_photo(photo=plot_file)
    else:
        await message.reply("Неправильный формат сообщения. Пример: чертила \"Зависимость скорости\" {V(м/c),T(с)} [1,2 2,3 3,4] сетка погрешность(1,1)")

# Запуск бота
async def main():
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == '__main__':
    asyncio.run(main())
