import http.server
import socketserver
import json
import webbrowser
import os
import sys
import threading
import time
from datetime import datetime, timedelta
import urllib.parse

PORT = 8080
DATA_FILE = "planner_data.json"

# Получение сегодняшней даты для дефолтных задач
today_str = datetime.now().strftime("%Y-%m-%d")
tomorrow_str = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

# Начальные данные, если файл planner_data.json еще не создан
DEFAULT_DATA = {
    "siteTitle": "Ежедневничек",
    "categories": ["Личная жизнь", "Учеба", "Здоровье", "Семья"],
    "tasks": [
        {
            "id": "1",
            "date": today_str,
            "text": "Запланировать дела на неделю",
            "category": "Личная жизнь",
            "completed": False,
        },
        {
            "id": "2",
            "date": tomorrow_str,
            "text": "Прочитать полезную статью",
            "category": "Учеба",
            "completed": False,
        },
    ],
}


def load_data():
    """Загрузка данных из JSON файла."""
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_DATA, f, ensure_ascii=False, indent=4)
        return DEFAULT_DATA
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return DEFAULT_DATA


def save_data(data):
    """Сохранение данных в JSON файл."""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


class PlannerRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # API для получения данных планировщика
        if self.path == "/api/data":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            data = load_data()
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
        else:
            # Во всех остальных случаях отдаем главную HTML-страницу
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode("utf-8"))

    def do_POST(self):
        # API для сохранения измененных данных
        if self.path == "/api/save":
            content_length = int(self.headers["Content-Length"])
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8"))
                save_data(data)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "ok"}).encode("utf-8"))
            except Exception as e:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(str(e).encode("utf-8"))

    def log_message(self, format, *args):
        # Отключаем лишний вывод логов в консоль для чистоты
        return


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ежедневничек — Планировщик задач</title>
    <!-- Tailwind CSS для стильного и быстрого оформления -->
    <script src="https://cdn.tailwindcss.com"></script>
    <!-- Подключение шрифта Inter и иконок Lucide -->
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <script src="https://unpkg.com/lucide@latest"></script>
    <style>
        body {
            font-family: 'Inter', sans-serif;
        }
    </style>
</head>
<body class="bg-white text-slate-800 min-h-screen flex flex-col">

    <header class="bg-white border-b border-slate-100 py-5 px-6 sticky top-0 z-10 shadow-sm">
        <div class="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
            <!-- Редактируемый Заголовок -->
            <div class="flex items-center gap-3">
                <div class="bg-indigo-50 p-2.5 rounded-xl text-indigo-600">
                    <i data-lucide="calendar-check" class="w-6 h-6"></i>
                </div>
                <div class="flex items-center gap-2 group">
                    <h1 id="site-title" class="text-2xl font-bold text-slate-900 tracking-tight">Ежедневничек</h1>
                    <button onclick="openEditTitleModal()" class="text-slate-400 hover:text-indigo-600 transition-colors p-1 rounded-lg hover:bg-slate-100" title="Изменить заголовок">
                        <i data-lucide="edit-2" class="w-4 h-4"></i>
                    </button>
                </div>
            </div>
            
            <!-- Кнопки управления категориями -->
            <div class="flex items-center gap-3">
                <button onclick="openCategoriesModal()" class="flex items-center gap-2 bg-slate-50 hover:bg-slate-100 text-slate-700 px-4 py-2 rounded-xl border border-slate-200 transition-all font-medium text-sm">
                    <i data-lucide="tag" class="w-4 h-4"></i>
                    Категории
                </button>
            </div>
        </div>
    </header>

    <main class="flex-grow max-w-[1400px] w-full mx-auto px-4 py-6 flex flex-col justify-center">
        <!-- Поля навигации по неделям слева и справа от сетки дней -->
        <div class="flex items-stretch gap-4 flex-grow">
            <!-- Кнопка Влево (Предыдущая неделя) -->
            <div class="flex items-center">
                <button onclick="changeWeek(-1)" class="h-12 w-12 rounded-full bg-white border border-slate-200 hover:border-indigo-400 text-slate-600 hover:text-indigo-600 transition-all shadow-sm hover:shadow flex items-center justify-center group" title="Предыдущая неделя">
                    <i data-lucide="chevron-left" class="w-6 h-6 group-hover:-translate-x-0.5 transition-transform"></i>
                </button>
            </div>

            <!-- Сетка дней недели -->
            <div class="flex-grow flex flex-col">
                <div id="current-week-label" class="text-center font-semibold text-slate-700 text-lg mb-6 tracking-wide">
                    Загрузка недели...
                </div>
                <div class="grid grid-cols-1 md:grid-cols-7 gap-4 items-start" id="days-container">
                    <!-- Колонки дней генерируются динамически через JavaScript -->
                </div>
            </div>

            <!-- Кнопка Вправо (Следующая неделя) -->
            <div class="flex items-center">
                <button onclick="changeWeek(1)" class="h-12 w-12 rounded-full bg-white border border-slate-200 hover:border-indigo-400 text-slate-600 hover:text-indigo-600 transition-all shadow-sm hover:shadow flex items-center justify-center group" title="Следующая неделя">
                    <i data-lucide="chevron-right" class="w-6 h-6 group-hover:translate-x-0.5 transition-transform"></i>
                </button>
            </div>
        </div>
    </main>

    <!-- Модальное окно задачи (Создание/Редактирование) -->
    <div id="task-modal" class="fixed inset-0 bg-slate-900/40 backdrop-blur-sm hidden items-center justify-center z-50 p-4">
        <div class="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl border border-slate-100">
            <div class="flex justify-between items-center mb-4">
                <h3 id="modal-title" class="text-lg font-bold text-slate-900">Добавить задачу</h3>
                <button onclick="closeTaskModal()" class="text-slate-400 hover:text-slate-600"><i data-lucide="x" class="w-5 h-5"></i></button>
            </div>
            <form id="task-form" onsubmit="saveTaskSubmit(event)" class="space-y-4">
                <input type="hidden" id="modal-task-id">
                <input type="hidden" id="modal-task-date">
                
                <div>
                    <label class="block text-xs font-semibold uppercase text-slate-500 mb-1">Текст задачи</label>
                    <input type="text" id="modal-task-text" required placeholder="Что нужно сделать?" class="w-full border border-slate-200 rounded-xl px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500">
                </div>

                <div>
                    <label class="block text-xs font-semibold uppercase text-slate-500 mb-1">Категория</label>
                    <select id="modal-task-category" class="w-full border border-slate-200 rounded-xl px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 bg-white">
                        <!-- Заполняется динамически -->
                    </select>
                </div>

                <div class="flex gap-2 justify-end pt-2">
                    <button type="button" onclick="closeTaskModal()" class="px-4 py-2 rounded-xl text-slate-600 hover:bg-slate-100 font-medium text-sm transition-all">Отмена</button>
                    <button type="submit" class="px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-medium text-sm shadow-sm transition-all">Сохранить</button>
                </div>
            </form>
        </div>
    </div>

    <!-- Модальное окно управления категориями -->
    <div id="categories-modal" class="fixed inset-0 bg-slate-900/40 backdrop-blur-sm hidden items-center justify-center z-50 p-4">
        <div class="bg-white rounded-2xl max-w-lg w-full p-6 shadow-xl border border-slate-100">
            <div class="flex justify-between items-center mb-4">
                <h3 class="text-lg font-bold text-slate-900">Управление категориями</h3>
                <button onclick="closeCategoriesModal()" class="text-slate-400 hover:text-slate-600"><i data-lucide="x" class="w-5 h-5"></i></button>
            </div>
            
            <!-- Форма добавления новой категории -->
            <div class="flex gap-2 mb-6">
                <input type="text" id="new-category-input" placeholder="Новая категория..." class="flex-grow border border-slate-200 rounded-xl px-4 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500">
                <button onclick="addCategory()" class="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-xl font-medium text-sm transition-all flex items-center gap-1">
                    <i data-lucide="plus" class="w-4 h-4"></i> Добавить
                </button>
            </div>

            <label class="block text-xs font-semibold uppercase text-slate-500 mb-2">Существующие категории</label>
            <div id="categories-list" class="space-y-2 max-h-64 overflow-y-auto pr-1">
                <!-- Категории рендерятся тут -->
            </div>

            <div class="flex justify-end pt-4 border-t border-slate-100 mt-4">
                <button onclick="closeCategoriesModal()" class="px-4 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-medium text-sm transition-all">Закрыть</button>
            </div>
        </div>
    </div>

    <!-- Модальное окно редактирования заголовка -->
    <div id="title-modal" class="fixed inset-0 bg-slate-900/40 backdrop-blur-sm hidden items-center justify-center z-50 p-4">
        <div class="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl border border-slate-100">
            <div class="flex justify-between items-center mb-4">
                <h3 class="text-lg font-bold text-slate-900">Изменить заголовок</h3>
                <button onclick="closeTitleModal()" class="text-slate-400 hover:text-slate-600"><i data-lucide="x" class="w-5 h-5"></i></button>
            </div>
            <div class="space-y-4">
                <input type="text" id="new-title-input" class="w-full border border-slate-200 rounded-xl px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500">
                <div class="flex gap-2 justify-end">
                    <button onclick="closeTitleModal()" class="px-4 py-2 rounded-xl text-slate-600 hover:bg-slate-100 font-medium text-sm transition-all">Отмена</button>
                    <button onclick="saveTitle()" class="px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-medium text-sm shadow-sm transition-all">Сохранить</button>
                </div>
            </div>
        </div>
    </div>

    <script>
        let state = {
            siteTitle: "Ежедневничек",
            categories: [],
            tasks: []
        };

        // Навигация по неделям
        let currentWeekOffset = 0; // 0 - текущая неделя, -1 - предыдущая, 1 - следующая

        // Получение первого дня недели (понедельника) по смещению
        function getMondayOfWeek(offset) {
            const today = new Date();
            const dayOfWeek = today.getDay(); // 0 - воскресенье, 1 - понедельник и т.д.
            const distanceToMonday = dayOfWeek === 0 ? -6 : 1 - dayOfWeek;
            const targetMonday = new Date(today);
            targetMonday.setDate(today.getDate() + distanceToMonday + (offset * 7));
            return targetMonday;
        }

        // Загрузка данных с бэкенда при запуске страницы
        async function fetchPlannerData() {
            try {
                const response = await fetch('/api/data');
                state = await response.json();
                renderAll();
            } catch (err) {
                console.error("Ошибка при получении данных:", err);
            }
        }

        // Сохранение изменений на сервер
        async function saveStateToServer() {
            try {
                await fetch('/api/save', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(state)
                });
                renderAll();
            } catch (err) {
                console.error("Ошибка при сохранении данных:", err);
            }
        }

        function renderAll() {
            // Обновляем заголовок сайта
            document.getElementById('site-title').innerText = state.siteTitle;

            const monday = getMondayOfWeek(currentWeekOffset);
            
            // Заголовок текущей недели в навигаторе
            const endOfWeek = new Date(monday);
            endOfWeek.setDate(monday.getDate() + 6);
            
            const options = { month: 'long', day: 'numeric' };
            const startLabel = monday.toLocaleDateString('ru-RU', options);
            const endLabel = endOfWeek.toLocaleDateString('ru-RU', options);
            document.getElementById('current-week-label').innerText = `${startLabel} — ${endLabel}`;

            // Генерация дней недели
            const daysContainer = document.getElementById('days-container');
            daysContainer.innerHTML = '';

            const dayNames = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье'];

            for (let i = 0; i < 7; i++) {
                const currentDay = new Date(monday);
                currentDay.setDate(monday.getDate() + i);
                
                const year = currentDay.getFullYear();
                const month = String(currentDay.getMonth() + 1).padStart(2, '0');
                const day = String(currentDay.getDate()).padStart(2, '0');
                const dateKey = `${year}-${month}-${day}`;

                // Форматируем заголовок в формате: "Число Месяц, День недели"
                const monthsRu = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря'];
                const formattedDateStr = `${currentDay.getDate()} ${monthsRu[currentDay.getMonth()]}, ${dayNames[i]}`;

                // Фильтруем задачи для этого дня
                const dayTasks = state.tasks.filter(t => t.date === dateKey);

                // Определение сегодняшнего дня
                const isToday = new Date().toDateString() === currentDay.toDateString();

                // Шаблон колонки дня
                const colHTML = `
                    <div class="bg-white rounded-2xl border ${isToday ? 'border-indigo-400 ring-4 ring-indigo-50' : 'border-slate-200'} shadow-sm flex flex-col overflow-hidden min-h-[400px] transition-all">
                        <!-- Шапка дня -->
                        <div class="p-4 border-b border-slate-100 flex justify-between items-start ${isToday ? 'bg-indigo-50/30' : 'bg-slate-50/30'}">
                            <div>
                                <h4 class="font-bold text-slate-800 text-sm tracking-tight">${formattedDateStr}</h4>
                                ${isToday ? '<span class="text-[10px] bg-indigo-600 text-white font-semibold px-2 py-0.5 rounded-full mt-1 inline-block uppercase">Сегодня</span>' : ''}
                            </div>
                            <button onclick="openAddTaskModal('${dateKey}')" class="p-1 rounded-lg bg-white border border-slate-200 text-indigo-600 hover:bg-indigo-50 hover:border-indigo-300 transition-all flex items-center justify-center shadow-sm" title="Добавить задачу">
                                <i data-lucide="plus" class="w-4 h-4"></i>
                            </button>
                        </div>
                        
                        <!-- Список задач -->
                        <div class="p-3 flex-grow space-y-2 max-h-[500px] overflow-y-auto">
                            ${dayTasks.length === 0 ? `
                                <div class="text-center py-12 text-slate-300 text-xs">
                                    <i data-lucide="inbox" class="w-8 h-8 mx-auto mb-1.5 opacity-40"></i>
                                    Нет дел
                                </div>
                            ` : dayTasks.map(task => `
                                <div class="group relative flex flex-col p-3 rounded-xl border ${task.completed ? 'bg-slate-50 border-slate-200' : 'bg-white border-slate-150 shadow-sm hover:border-slate-300'} transition-all gap-1.5">
                                    <div class="flex items-start gap-2.5">
                                        <input type="checkbox" ${task.completed ? 'checked' : ''} 
                                            onclick="toggleTaskComplete('${task.id}')" 
                                            class="mt-1 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500/30 w-4 h-4 cursor-pointer">
                                        <span class="text-sm font-medium leading-tight text-slate-700 ${task.completed ? 'line-through text-slate-400' : ''} break-all pr-12">
                                            ${escapeHTML(task.text)}
                                        </span>
                                    </div>
                                    
                                    <!-- Категория под задачей серым цветом -->
                                    <div class="flex items-center gap-1 pl-6.5 text-[11px] font-medium text-slate-400">
                                        <i data-lucide="tag" class="w-3 h-3"></i>
                                        <span>${escapeHTML(task.category || 'Без категории')}</span>
                                    </div>

                                    <!-- Кнопки управления (Изменить, Удалить) - появляются на десктопе при наведении -->
                                    <div class="absolute right-2 top-2 flex items-center gap-1 md:opacity-0 group-hover:opacity-100 transition-opacity bg-white/95 py-0.5 px-1 rounded-lg shadow-sm border border-slate-100">
                                        <button onclick="openEditTaskModal('${task.id}')" class="p-1 hover:text-indigo-600 text-slate-400 rounded transition-all" title="Изменить">
                                            <i data-lucide="edit-3" class="w-3.5 h-3.5"></i>
                                        </button>
                                        <button onclick="deleteTask('${task.id}')" class="p-1 hover:text-rose-600 text-slate-400 rounded transition-all" title="Удалить">
                                            <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
                                        </button>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                `;
                daysContainer.innerHTML += colHTML;
            }

            // Переинициализация иконок Lucide
            lucide.createIcons();
        }

        // Вспомогательная функция против XSS
        function escapeHTML(str) {
            return str.replace(/[&<>'"]/g, 
                tag => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[tag] || tag)
            );
        }

        // Смена недели
        function changeWeek(direction) {
            currentWeekOffset += direction;
            renderAll();
        }

        function openAddTaskModal(dateStr) {
            document.getElementById('modal-title').innerText = "Добавить задачу";
            document.getElementById('modal-task-id').value = "";
            document.getElementById('modal-task-date').value = dateStr;
            document.getElementById('modal-task-text').value = "";
            
            fillCategorySelect();
            
            document.getElementById('task-modal').classList.remove('hidden');
            document.getElementById('task-modal').classList.add('flex');
        }

        function openEditTaskModal(id) {
            const task = state.tasks.find(t => t.id === id);
            if (!task) return;

            document.getElementById('modal-title').innerText = "Изменить задачу";
            document.getElementById('modal-task-id').value = task.id;
            document.getElementById('modal-task-date').value = task.date;
            document.getElementById('modal-task-text').value = task.text;

            fillCategorySelect(task.category);

            document.getElementById('task-modal').classList.remove('hidden');
            document.getElementById('task-modal').classList.add('flex');
        }

        function closeTaskModal() {
            document.getElementById('task-modal').classList.remove('flex');
            document.getElementById('task-modal').classList.add('hidden');
        }

        function fillCategorySelect(selectedCategory = "") {
            const select = document.getElementById('modal-task-category');
            select.innerHTML = '<option value="">Без категории</option>';
            state.categories.forEach(cat => {
                const isSelected = cat === selectedCategory ? 'selected' : '';
                select.innerHTML += `<option value="${escapeHTML(cat)}" ${isSelected}>${escapeHTML(cat)}</option>`;
            });
        }

        function saveTaskSubmit(event) {
            event.preventDefault();
            const id = document.getElementById('modal-task-id').value;
            const date = document.getElementById('modal-task-date').value;
            const text = document.getElementById('modal-task-text').value.trim();
            const category = document.getElementById('modal-task-category').value;

            if (!text) return;

            if (id) {
                // Редактирование существующей
                const task = state.tasks.find(t => t.id === id);
                if (task) {
                    task.text = text;
                    task.category = category;
                }
            } else {
                // Создание новой
                const newTask = {
                    id: Date.now().toString(),
                    date: date,
                    text: text,
                    category: category,
                    completed: false
                };
                state.tasks.push(newTask);
            }

            closeTaskModal();
            saveStateToServer();
        }

        function toggleTaskComplete(id) {
            const task = state.tasks.find(t => t.id === id);
            if (task) {
                task.completed = !task.completed;
                saveStateToServer();
            }
        }

        function deleteTask(id) {
            state.tasks = state.tasks.filter(t => t.id !== id);
            saveStateToServer();
        }

        // Управление категориями
        function openCategoriesModal() {
            renderCategoriesList();
            document.getElementById('categories-modal').classList.remove('hidden');
            document.getElementById('categories-modal').classList.add('flex');
        }

        function closeCategoriesModal() {
            document.getElementById('categories-modal').classList.remove('flex');
            document.getElementById('categories-modal').classList.add('hidden');
        }

        function renderCategoriesList() {
            const list = document.getElementById('categories-list');
            list.innerHTML = '';
            
            if (state.categories.length === 0) {
                list.innerHTML = '<div class="text-sm text-slate-400 py-2">Нет добавленных категорий.</div>';
                return;
            }

            state.categories.forEach((cat, index) => {
                list.innerHTML += `
                    <div class="flex items-center justify-between bg-slate-50 p-3 rounded-xl border border-slate-100">
                        <span class="font-medium text-slate-700 text-sm">${escapeHTML(cat)}</span>
                        <div class="flex gap-1">
                            <button onclick="editCategoryPrompt('${escapeHTML(cat)}')" class="p-1.5 hover:bg-indigo-50 hover:text-indigo-600 text-slate-400 rounded-lg transition-all" title="Изменить">
                                <i data-lucide="edit-3" class="w-4 h-4"></i>
                            </button>
                            <button onclick="deleteCategory('${escapeHTML(cat)}')" class="p-1.5 hover:bg-rose-50 hover:text-rose-600 text-slate-400 rounded-lg transition-all" title="Удалить">
                                <i data-lucide="trash-2" class="w-4 h-4"></i>
                            </button>
                        </div>
                    </div>
                `;
            });
            lucide.createIcons();
        }

        function addCategory() {
            const input = document.getElementById('new-category-input');
            const newCat = input.value.trim();
            if (!newCat) return;

            if (state.categories.includes(newCat)) {
                alert("Такая категория уже существует!");
                return;
            }

            state.categories.push(newCat);
            input.value = "";
            renderCategoriesList();
            saveStateToServer();
        }

        function editCategoryPrompt(oldName) {
            const newName = prompt("Введите новое название для категории:", oldName);
            if (newName === null) return;
            const trimmed = newName.trim();
            if (!trimmed || trimmed === oldName) return;

            if (state.categories.includes(trimmed)) {
                alert("Категория с таким названием уже есть!");
                return;
            }

            // Переименовываем саму категорию
            const index = state.categories.indexOf(oldName);
            if (index !== -1) {
                state.categories[index] = trimmed;
            }

            // Обновляем категорию во всех привязанных задачах
            state.tasks.forEach(t => {
                if (t.category === oldName) {
                    t.category = trimmed;
                }
            });

            renderCategoriesList();
            saveStateToServer();
        }

        function deleteCategory(catName) {
            if (!confirm(`Вы уверены, что хотите удалить категорию "${catName}"?`)) return;

            state.categories = state.categories.filter(c => c !== catName);
            
            // Задачи с этой категорией сбрасываем в "Без категории"
            state.tasks.forEach(t => {
                if (t.category === catName) {
                    t.category = "";
                }
            });

            renderCategoriesList();
            saveStateToServer();
        }

        // Изменение заголовка
        function openEditTitleModal() {
            document.getElementById('new-title-input').value = state.siteTitle;
            document.getElementById('title-modal').classList.remove('hidden');
            document.getElementById('title-modal').classList.add('flex');
        }

        function closeTitleModal() {
            document.getElementById('title-modal').classList.remove('flex');
            document.getElementById('title-modal').classList.add('hidden');
        }

        function saveTitle() {
            const newTitle = document.getElementById('new-title-input').value.trim();
            if (!newTitle) return;

            state.siteTitle = newTitle;
            closeTitleModal();
            saveStateToServer();
        }

        // Первичная загрузка при открытии
        fetchPlannerData();
    </script>
</body>
</html>
"""


def open_browser():
    """Открывает браузер после небольшой паузы, чтобы сервер успел запуститься."""
    time.sleep(1.5)
    webbrowser.open(f"http://localhost:{PORT}")


if __name__ == "__main__":
    # Запускаем фоновый поток для открытия браузера
    threading.Thread(target=open_browser, daemon=True).start()

    print(f"Запускаем сервер на порту {PORT}...")
    print(f"Если браузер не открылся сам, перейдите по ссылке: http://localhost:{PORT}")

    server_address = ("", PORT)
    httpd = socketserver.TCPServer(server_address, PlannerRequestHandler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nСервер остановлен.")
        sys.exit(0)
