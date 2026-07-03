import http.server
import socketserver
import json
import webbrowser
import os
import sys
import threading
import time
from datetime import datetime, timedelta

PORT = 8080
DATA_FILE = "planner_data.json"

today_str = datetime.now().strftime("%Y-%m-%d")
tomorrow_str = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

DEFAULT_DATA = {
    "siteTitle": "Ежедневничек",
    "motivationalImage": "",
    "bannerX": 0,
    "bannerY": 0,
    "bannerScale": 1.0,
    "categories": [
        {"name": "Личная жизнь", "color": "#3b82f6"},
        {"name": "Учеба", "color": "#f59e0b"},
        {"name": "Здоровье", "color": "#10b981"},
        {"name": "Семья", "color": "#ef4444"}
    ],
    "tasks": [
        {
            "id": "1", 
            "date": today_str, 
            "text": "Запланировать дела на неделю и поставить амбициозные цели", 
            "categories": ["Личная жизнь"], 
            "completed": False,
            "deadlineDate": today_str,
            "deadlineTime": "18:00"
        }
    ],
    "goals": [
        {
            "id": "g1",
            "name": "Изучить основы Python",
            "addedDate": int(time.time() * 1000),
            "checklist": [
                {"id": "s1", "text": "Установить интерпретатор Python", "completed": True},
                {"id": "s2", "text": "Разобраться с переменными и циклами", "completed": False}
            ]
        }
    ],
    "notesList": [
        {
            "id": "n1",
            "title": "Общие заметки",
            "content": "<div>Добро пожаловать в ваши личные <b>заметки</b>!</div><div>Здесь можно записывать любые мысли, важные идеи и вставлять картинки.</div>",
            "collapsed": False
        }
    ]
}

def load_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_DATA, f, ensure_ascii=False, indent=4)
        return DEFAULT_DATA
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            
            # Миграции структуры данных
            if "notesList" not in data:
                old_notes = data.get("notes", "<div>Начните писать здесь...</div>")
                data["notesList"] = [
                    {
                        "id": "n_default",
                        "title": "Первая заметка",
                        "content": old_notes,
                        "collapsed": False
                    }
                ]
                if "notes" in data:
                    del data["notes"]
            
            if "bannerX" not in data:
                data["bannerX"] = 0
            if "bannerY" not in data:
                data["bannerY"] = 0
            if "bannerScale" not in data:
                data["bannerScale"] = 1.0

            if "goals" not in data:
                data["goals"] = DEFAULT_DATA["goals"]
            else:
                for idx, g in enumerate(data["goals"]):
                    if "addedDate" not in g:
                        g["addedDate"] = int(time.time() * 1000) - (len(data["goals"]) - idx) * 1000
            
            if "siteTitle" not in data:
                data["siteTitle"] = "Ежедневничек"
            if "categories" not in data:
                data["categories"] = DEFAULT_DATA["categories"]
            if "tasks" not in data:
                data["tasks"] = DEFAULT_DATA["tasks"]
                
            return data
    except Exception:
        return DEFAULT_DATA

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

class PlannerRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/data":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.end_headers()
            data = load_data()
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
        else:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode("utf-8"))

    def do_POST(self):
        if self.path == "/api/save":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
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
        return

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ежедневничек — Персональный планировщик</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <script src="https://unpkg.com/lucide@latest"></script>
    <style>
        body { font-family: 'Inter', sans-serif; }
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: #94a3b8; }
        .drag-over-goal { border: 2px dashed #6366f1 !important; background-color: #f5f3ff !important; }
    </style>
</head>
<body class="bg-white text-slate-800 min-h-screen flex select-none">

    <aside id="sidebar" class="fixed left-0 top-0 h-screen w-16 hover:w-60 bg-slate-900 text-slate-400 flex flex-col justify-between py-6 shadow-2xl z-40 transition-all duration-300 ease-in-out group overflow-hidden shrink-0">
        <div class="flex flex-col gap-8">
            <div class="flex items-center gap-4 px-5">
                <div class="p-1 bg-indigo-600 rounded-xl text-white flex items-center justify-center shrink-0">
                    <i data-lucide="sparkles" class="w-6 h-6"></i>
                </div>
                <span class="font-bold text-white tracking-wider text-base opacity-0 group-hover:opacity-100 transition-opacity duration-300 whitespace-nowrap">ПЛАНИРОВЩИК</span>
            </div>

            <nav class="flex flex-col gap-2 px-3">
                <button onclick="switchTab('main')" id="tab-main-btn" class="flex items-center gap-4 py-3 px-3.5 rounded-xl hover:bg-slate-800 text-slate-300 hover:text-white transition-all w-full text-left bg-slate-800 text-white">
                    <i data-lucide="calendar" class="w-5 h-5 shrink-0 text-indigo-400"></i>
                    <span class="font-semibold text-sm opacity-0 group-hover:opacity-100 transition-opacity duration-300 whitespace-nowrap">Главная</span>
                </button>
                <button onclick="switchTab('goals')" id="tab-goals-btn" class="flex items-center gap-4 py-3 px-3.5 rounded-xl hover:bg-slate-800 text-slate-300 hover:text-white transition-all w-full text-left">
                    <i data-lucide="target" class="w-5 h-5 shrink-0 text-amber-400"></i>
                    <span class="font-semibold text-sm opacity-0 group-hover:opacity-100 transition-opacity duration-300 whitespace-nowrap">Цели</span>
                </button>
                <button onclick="switchTab('notes')" id="tab-notes-btn" class="flex items-center gap-4 py-3 px-3.5 rounded-xl hover:bg-slate-800 text-slate-300 hover:text-white transition-all w-full text-left">
                    <i data-lucide="file-text" class="w-5 h-5 shrink-0 text-emerald-400"></i>
                    <span class="font-semibold text-sm opacity-0 group-hover:opacity-100 transition-opacity duration-300 whitespace-nowrap">Заметки</span>
                </button>
            </nav>
        </div>

        <div class="px-5 text-xs text-slate-500 flex items-center gap-4 whitespace-nowrap overflow-hidden">
            <i data-lucide="info" class="w-5 h-5 shrink-0"></i>
            <span class="opacity-0 group-hover:opacity-100 transition-opacity duration-300">v3.8 • Стабильный</span>
        </div>
    </aside>

    <div class="flex-grow ml-16 min-h-screen flex flex-col transition-all duration-300 overflow-x-hidden">
        
        <header class="bg-white border-b border-slate-100 py-4 px-6 sticky top-0 z-30 shadow-sm">
            <div class="max-w-[98vw] mx-auto flex items-center justify-between gap-4">
                <div class="flex items-center gap-3">
                    <div class="bg-indigo-50 p-2 rounded-xl text-indigo-600">
                        <i data-lucide="calendar-check" class="w-5 h-5"></i>
                    </div>
                    <div class="flex items-center gap-2">
                        <h1 id="site-title" class="text-xl font-bold text-slate-900 tracking-tight">Ежедневничек</h1>
                        <button onclick="openEditTitleModal()" class="text-slate-400 hover:text-indigo-600 transition-colors p-1 rounded-lg hover:bg-slate-100" title="Изменить заголовок">
                            <i data-lucide="edit-2" class="w-4 h-4"></i>
                        </button>
                    </div>
                </div>
                
                <div id="header-actions" class="flex items-center gap-3">
                    <button onclick="openCategoriesModal()" class="flex items-center gap-2 bg-slate-50 hover:bg-slate-100 text-slate-700 px-4 py-2 rounded-xl border border-slate-200 transition-all font-medium text-sm">
                        <i data-lucide="tag" class="w-4 h-4"></i>
                        Категории
                    </button>
                </div>
            </div>
        </header>

        <main id="view-main" class="flex-grow max-w-[98vw] w-full mx-auto px-2 py-6 flex flex-col justify-start">
            <div id="motivational-banner" class="mb-6 w-full relative"></div>
            <input type="file" id="banner-file-input" class="hidden" accept="image/*" onchange="uploadBanner(event)">

            <div class="flex items-stretch gap-2 flex-grow">
                <div class="flex items-center">
                    <button onclick="changeWeek(-1)" class="h-12 w-12 rounded-full bg-white border border-slate-200 hover:border-indigo-400 text-slate-600 hover:text-indigo-600 transition-all shadow-sm hover:shadow flex items-center justify-center group" title="Предыдущая неделя">
                        <i data-lucide="chevron-left" class="w-6 h-6 group-hover:-translate-x-0.5 transition-transform"></i>
                    </button>
                </div>

                <div class="flex-grow flex flex-col">
                    <div onclick="openMonthCalendarModal()" id="current-week-label" class="text-center font-bold text-slate-700 text-lg mb-6 tracking-wide uppercase text-sm cursor-pointer hover:text-indigo-600 transition-colors flex items-center justify-center gap-2" title="Открыть календарь месяца">
                        <span>Загрузка недели...</span>
                        <i data-lucide="calendar-days" class="w-4 h-4 text-indigo-500"></i>
                    </div>
                    <div class="grid grid-cols-1 md:grid-cols-7 gap-3 items-start" id="days-container"></div>
                </div>

                <div class="flex items-center">
                    <button onclick="changeWeek(1)" class="h-12 w-12 rounded-full bg-white border border-slate-200 hover:border-indigo-400 text-slate-600 hover:text-indigo-600 transition-all shadow-sm hover:shadow flex items-center justify-center group" title="Следующая неделя">
                        <i data-lucide="chevron-right" class="w-6 h-6 group-hover:translate-x-0.5 transition-transform"></i>
                    </button>
                </div>
            </div>
        </main>

        <main id="view-goals" class="hidden flex-grow max-w-[98vw] w-full mx-auto px-6 py-6 flex flex-col">
            <div class="flex justify-between items-center mb-6">
                <div>
                    <h2 class="text-2xl font-bold text-slate-950">Мои Цели</h2>
                    <p class="text-sm text-slate-500">Достигайте больших результатов, разбивая их на простые чек-листы</p>
                </div>
                <div class="flex items-center gap-3">
                    <div class="relative inline-block text-left group">
                        <button class="flex items-center gap-2 bg-slate-50 hover:bg-slate-100 text-slate-700 px-4 py-2.5 rounded-xl border border-slate-200 transition-all font-semibold text-sm">
                            <i data-lucide="arrow-up-down" class="w-4 h-4 text-indigo-500"></i>
                            <span id="sort-label-text">Сортировка: Произвольно</span>
                        </button>
                        <div class="absolute right-0 w-64 bg-white border border-slate-200 rounded-2xl shadow-xl py-1.5 hidden group-hover:block z-50">
                            <button onclick="setGoalsSort('alphabet')" class="flex items-center justify-between px-4 py-2 hover:bg-indigo-50 hover:text-indigo-600 w-full text-left font-semibold text-xs text-slate-700">
                                <span>По алфавиту (А-Я / Я-А)</span>
                                <i data-lucide="sort-asc" class="w-3.5 h-3.5 opacity-60"></i>
                            </button>
                            <button onclick="setGoalsSort('date')" class="flex items-center justify-between px-4 py-2 hover:bg-indigo-50 hover:text-indigo-600 w-full text-left font-semibold text-xs text-slate-700">
                                <span>По дате добавления (Новые/Старые)</span>
                                <i data-lucide="calendar" class="w-3.5 h-3.5 opacity-60"></i>
                            </button>
                            <button onclick="setGoalsSort('progress')" class="flex items-center justify-between px-4 py-2 hover:bg-indigo-50 hover:text-indigo-600 w-full text-left font-semibold text-xs text-slate-700">
                                <span>По прогрессу (Убывание/Возрастание)</span>
                                <i data-lucide="trending-up" class="w-3.5 h-3.5 opacity-60"></i>
                            </button>
                            <button onclick="setGoalsSort('manual')" class="flex items-center justify-between px-4 py-2 hover:bg-indigo-50 hover:text-indigo-600 w-full text-left font-semibold text-xs text-slate-700">
                                <span>Произвольно (Вручную)</span>
                                <i data-lucide="move" class="w-3.5 h-3.5 opacity-60"></i>
                            </button>
                        </div>
                    </div>

                    <button onclick="openAddGoalModal()" class="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2.5 rounded-xl font-medium text-sm shadow-sm transition-all">
                        <i data-lucide="plus" class="w-4 h-4"></i> Добавить цель
                    </button>
                </div>
            </div>

            <div id="goals-container" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"></div>
        </main>

        <main id="view-notes" class="hidden flex-grow max-w-[98vw] w-full mx-auto px-6 py-6 flex flex-col">
            <div class="flex justify-between items-center mb-4">
                <div>
                    <h2 class="text-2xl font-bold text-slate-950 mb-1">Заметки и мысли</h2>
                    <p class="text-sm text-slate-500">Пишите важные идеи, конспекты и выделяйте нужные слова.</p>
                </div>
                <button onclick="addNote()" class="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2.5 rounded-xl font-medium text-sm shadow-sm transition-all">
                    <i data-lucide="plus" class="w-4 h-4"></i> Создать заметку
                </button>
            </div>

            <div class="bg-slate-50 border border-slate-200 rounded-2xl p-4 mb-4 flex flex-wrap items-center gap-4 sticky top-[72px] z-20">
                <span class="text-xs font-semibold uppercase text-slate-500 tracking-wider flex items-center gap-1.5">
                    <i data-lucide="highlighter" class="w-4 h-4 text-indigo-500"></i> Маркер:
                </span>
                <div class="flex flex-wrap items-center gap-2">
                    <button onclick="applyHighlight('#ff5c5c')" class="w-8 h-8 rounded-full border border-red-500 bg-[#ff5c5c] hover:scale-110 active:scale-95 transition-transform" title="Красный"></button>
                    <button onclick="applyHighlight('#ff922b')" class="w-8 h-8 rounded-full border border-orange-500 bg-[#ff922b] hover:scale-110 active:scale-95 transition-transform" title="Оранжевый"></button>
                    <button onclick="applyHighlight('#fcc419')" class="w-8 h-8 rounded-full border border-yellow-500 bg-[#fcc419] hover:scale-110 active:scale-95 transition-transform" title="Желтый"></button>
                    <button onclick="applyHighlight('#51cf66')" class="w-8 h-8 rounded-full border border-green-500 bg-[#51cf66] hover:scale-110 active:scale-95 transition-transform" title="Зеленый"></button>
                    <button onclick="applyHighlight('#339af0')" class="w-8 h-8 rounded-full border border-blue-500 bg-[#339af0] hover:scale-110 active:scale-95 transition-transform" title="Синий"></button>
                    <button onclick="applyHighlight('#cc5de8')" class="w-8 h-8 rounded-full border border-purple-500 bg-[#cc5de8] hover:scale-110 active:scale-95 transition-transform" title="Фиолетовый"></button>
                    <button onclick="applyHighlight('#868e96')" class="w-8 h-8 rounded-full border border-slate-500 bg-[#868e96] hover:scale-110 active:scale-95 transition-transform" title="Серый"></button>
                    
                    <span class="h-6 w-[1px] bg-slate-300 mx-1"></span>

                    <button onclick="clearHighlight()" class="px-3 py-1 bg-white border border-slate-200 hover:border-slate-300 text-xs font-semibold text-slate-600 rounded-xl flex items-center gap-1.5 hover:bg-slate-50 transition-all mr-2">
                        <i data-lucide="eraser" class="w-3.5 h-3.5"></i> Убрать
                    </button>

                    <span class="h-6 w-[1px] bg-slate-300 mx-1"></span>

                    <button id="btn-format-bold" onclick="formatNote('bold')" class="p-2 bg-white hover:bg-slate-100 border border-slate-200 rounded-xl transition-all" title="Жирный"><i data-lucide="bold" class="w-4 h-4"></i></button>
                    <button id="btn-format-italic" onclick="formatNote('italic')" class="p-2 bg-white hover:bg-slate-100 border border-slate-200 rounded-xl transition-all" title="Курсив"><i data-lucide="italic" class="w-4 h-4"></i></button>
                    <button id="btn-format-strike" onclick="formatNote('strikeThrough')" class="p-2 bg-white hover:bg-slate-100 border border-slate-200 rounded-xl transition-all" title="Зачеркнутый"><i data-lucide="strikethrough" class="w-4 h-4"></i></button>
                    
                    <span class="h-6 w-[1px] bg-slate-300 mx-1"></span>

                    <button onclick="triggerImageInsert()" class="p-2 bg-white hover:bg-indigo-50 border border-indigo-200 text-indigo-600 rounded-xl transition-all flex items-center gap-1 text-xs font-semibold" title="Вставить изображение в заметку">
                        <i data-lucide="image" class="w-4 h-4"></i> Изображение
                    </button>
                    <input type="file" id="note-image-input" class="hidden" accept="image/*" onchange="insertImageInNote(event)">
                </div>
            </div>

            <div id="notes-stack" class="space-y-4"></div>
        </main>
    </div>

    <!-- Тулбар для картинок (ABSOLUTE) -->
    <div id="image-toolbar" class="absolute hidden bg-slate-950/95 text-white border border-slate-800 rounded-full shadow-2xl z-50 p-1.5 items-center gap-2 text-[10px] font-bold">
        <button onclick="resizeSelectedImage(0.8)" class="px-2.5 py-1.5 hover:bg-slate-800 rounded-full transition-all">Меньше (-)</button>
        <button onclick="resizeSelectedImage(1.2)" class="px-2.5 py-1.5 hover:bg-slate-800 rounded-full transition-all">Больше (+)</button>
        <span class="h-4 w-[1px] bg-slate-700"></span>
        <button onclick="setSelectedImagePercent(25)" class="px-2.5 py-1.5 hover:bg-slate-800 rounded-full transition-all">25%</button>
        <button onclick="setSelectedImagePercent(50)" class="px-2.5 py-1.5 hover:bg-slate-800 rounded-full transition-all">50%</button>
        <button onclick="setSelectedImagePercent(100)" class="px-2.5 py-1.5 hover:bg-slate-800 rounded-full transition-all">100%</button>
        <span class="h-4 w-[1px] bg-slate-700"></span>
        <button onclick="deleteSelectedImage()" class="px-2.5 py-1.5 bg-rose-600/30 text-rose-400 hover:bg-rose-600 hover:text-white rounded-full transition-all">Удалить</button>
    </div>

    <!-- Меню правого клика (ABSOLUTE) -->
    <div id="image-context-menu" class="absolute hidden bg-white border border-slate-200 rounded-xl shadow-2xl z-50 py-1.5 w-56 text-slate-700 text-xs font-semibold">
        <button onclick="imageAction('align-left')" class="flex items-center gap-2 px-3 py-2 hover:bg-indigo-50 hover:text-indigo-600 w-full text-left">
            <i data-lucide="align-left" class="w-3.5 h-3.5"></i> Слева от текста
        </button>
        <button onclick="imageAction('align-right')" class="flex items-center gap-2 px-3 py-2 hover:bg-indigo-50 hover:text-indigo-600 w-full text-left">
            <i data-lucide="align-right" class="w-3.5 h-3.5"></i> Справа от текста
        </button>
        <button onclick="imageAction('align-center')" class="flex items-center gap-2 px-3 py-2 hover:bg-indigo-50 hover:text-indigo-600 w-full text-left">
            <i data-lucide="align-justify" class="w-3.5 h-3.5"></i> Отдельной строкой
        </button>
        <hr class="my-1 border-slate-100" />
        <button onclick="imageAction('copy')" class="flex items-center gap-2 px-3 py-2 hover:bg-indigo-50 hover:text-indigo-600 w-full text-left">
            <i data-lucide="copy" class="w-3.5 h-3.5"></i> Скопировать
        </button>
        <button onclick="imageAction('cut')" class="flex items-center gap-2 px-3 py-2 hover:bg-indigo-50 hover:text-indigo-600 w-full text-left">
            <i data-lucide="scissors" class="w-3.5 h-3.5"></i> Вырезать
        </button>
        <button id="ctx-paste-btn" onclick="imageAction('paste')" class="flex items-center gap-2 px-3 py-2 hover:bg-indigo-50 hover:text-indigo-600 w-full text-left">
            <i data-lucide="clipboard" class="w-3.5 h-3.5"></i> Вставить
        </button>
        <button onclick="imageAction('border')" class="flex items-center gap-2 px-3 py-2 hover:bg-indigo-50 hover:text-indigo-600 w-full text-left">
            <i data-lucide="square" class="w-3.5 h-3.5"></i> Обводка
        </button>
        <button onclick="imageAction('rotate')" class="flex items-center gap-2 px-3 py-2 hover:bg-indigo-50 hover:text-indigo-600 w-full text-left">
            <i data-lucide="rotate-cw" class="w-3.5 h-3.5"></i> Повернуть на 90°
        </button>
        <hr class="my-1 border-slate-100" />
        <button onclick="imageAction('delete')" class="flex items-center gap-2 px-3 py-2 text-rose-600 hover:bg-rose-50 w-full text-left">
            <i data-lucide="trash-2" class="w-3.5 h-3.5"></i> Удалить
        </button>
    </div>

    <!-- Модалки -->
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
                    <textarea id="modal-task-text" required placeholder="Что нужно сделать?" rows="3" class="w-full border border-slate-200 rounded-xl px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 text-sm font-medium"></textarea>
                </div>

                <div>
                    <label class="block text-xs font-semibold uppercase text-slate-500 mb-1">Категории</label>
                    <div id="modal-categories-list" class="max-h-28 overflow-y-auto p-2 border border-slate-200 rounded-xl space-y-1.5"></div>
                </div>

                <div class="grid grid-cols-2 gap-3">
                    <div>
                        <label class="block text-xs font-semibold uppercase text-slate-500 mb-1">Срок до (Дата)</label>
                        <input type="date" id="modal-task-deadline-date" class="w-full border border-slate-200 rounded-xl px-3 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 bg-white">
                    </div>
                    <div>
                        <label class="block text-xs font-semibold uppercase text-slate-500 mb-1">Срок до (Время)</label>
                        <input type="time" id="modal-task-deadline-time" class="w-full border border-slate-200 rounded-xl px-3 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 bg-white">
                    </div>
                </div>

                <div class="flex gap-2 justify-end pt-2">
                    <button type="button" onclick="closeTaskModal()" class="px-4 py-2 rounded-xl text-slate-600 hover:bg-slate-100 font-medium text-sm transition-all">Отмена</button>
                    <button type="submit" class="px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-medium text-sm shadow-sm transition-all">Сохранить</button>
                </div>
            </form>
        </div>
    </div>

    <div id="categories-modal" class="fixed inset-0 bg-slate-900/40 backdrop-blur-sm hidden items-center justify-center z-50 p-4">
        <div class="bg-white rounded-2xl max-w-lg w-full p-6 shadow-xl border border-slate-100">
            <div class="flex justify-between items-center mb-4">
                <h3 class="text-lg font-bold text-slate-900">Управление категориями</h3>
                <button onclick="closeCategoriesModal()" class="text-slate-400 hover:text-slate-600"><i data-lucide="x" class="w-5 h-5"></i></button>
            </div>
            
            <div class="flex gap-2 mb-6 items-center">
                <input type="text" id="new-category-input" placeholder="Новая категория..." class="flex-grow border border-slate-200 rounded-xl px-4 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 text-sm">
                <input type="color" id="new-category-color" value="#6366f1" class="w-10 h-10 border border-slate-200 rounded-xl cursor-pointer p-1" title="Выберите цвет">
                <button onclick="addCategory()" class="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 h-10 rounded-xl font-medium text-sm transition-all flex items-center gap-1 shrink-0">
                    <i data-lucide="plus" class="w-4 h-4"></i> Добавить
                </button>
            </div>

            <label class="block text-xs font-semibold uppercase text-slate-500 mb-2">Существующие категории</label>
            <div id="categories-list" class="space-y-2 max-h-64 overflow-y-auto pr-1"></div>

            <div class="flex justify-end pt-4 border-t border-slate-100 mt-4">
                <button onclick="closeCategoriesModal()" class="px-4 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-medium text-sm transition-all">Закрыть</button>
            </div>
        </div>
    </div>

    <div id="edit-category-modal" class="fixed inset-0 bg-slate-900/40 backdrop-blur-sm hidden items-center justify-center z-50 p-4">
        <div class="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl border border-slate-100">
            <div class="flex justify-between items-center mb-4">
                <h3 class="text-lg font-bold text-slate-900">Изменить категорию</h3>
                <button onclick="closeEditCategoryModal()" class="text-slate-400 hover:text-slate-600"><i data-lucide="x" class="w-5 h-5"></i></button>
            </div>
            <div class="space-y-4">
                <input type="hidden" id="edit-category-old-name">
                <div>
                    <label class="block text-xs font-semibold uppercase text-slate-500 mb-1">Название категории</label>
                    <input type="text" id="edit-category-name-input" class="w-full border border-slate-200 rounded-xl px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 text-sm">
                </div>
                <div>
                    <label class="block text-xs font-semibold uppercase text-slate-500 mb-1">Цвет категории</label>
                    <input type="color" id="edit-category-color-input" class="w-full h-11 border border-slate-200 rounded-xl cursor-pointer p-1">
                </div>
                <div class="flex gap-2 justify-end">
                    <button onclick="closeEditCategoryModal()" class="px-4 py-2 rounded-xl text-slate-600 hover:bg-slate-100 font-medium text-sm transition-all">Отмена</button>
                    <button onclick="saveCategoryEdit()" class="px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-medium text-sm shadow-sm transition-all">Сохранить</button>
                </div>
            </div>
        </div>
    </div>

    <div id="title-modal" class="fixed inset-0 bg-slate-900/40 backdrop-blur-sm hidden items-center justify-center z-50 p-4">
        <div class="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl border border-slate-100">
            <div class="flex justify-between items-center mb-4">
                <h3 class="text-lg font-bold text-slate-900">Изменить заголовок</h3>
                <button onclick="closeTitleModal()" class="text-slate-400 hover:text-slate-600"><i data-lucide="x" class="w-5 h-5"></i></button>
            </div>
            <div class="space-y-4">
                <input type="text" id="new-title-input" class="w-full border border-slate-200 rounded-xl px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 text-sm">
                <div class="flex gap-2 justify-end">
                    <button onclick="closeTitleModal()" class="px-4 py-2 rounded-xl text-slate-600 hover:bg-slate-100 font-medium text-sm transition-all">Отмена</button>
                    <button onclick="saveTitle()" class="px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-medium text-sm shadow-sm transition-all">Сохранить</button>
                </div>
            </div>
        </div>
    </div>

    <div id="goal-modal" class="fixed inset-0 bg-slate-900/40 backdrop-blur-sm hidden items-center justify-center z-50 p-4">
        <div class="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl border border-slate-100">
            <div class="flex justify-between items-center mb-4">
                <h3 class="text-lg font-bold text-slate-900">Добавить новую цель</h3>
                <button onclick="closeGoalModal()" class="text-slate-400 hover:text-slate-600"><i data-lucide="x" class="w-5 h-5"></i></button>
            </div>
            <form onsubmit="saveGoalSubmit(event)" class="space-y-4">
                <div>
                    <label class="block text-xs font-semibold uppercase text-slate-500 mb-1">Название цели</label>
                    <input type="text" id="modal-goal-name" required placeholder="Например: Прочесть 10 книг" class="w-full border border-slate-200 rounded-xl px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 text-sm font-medium">
                </div>
                <div class="flex gap-2 justify-end pt-2">
                    <button type="button" onclick="closeGoalModal()" class="px-4 py-2 rounded-xl text-slate-600 hover:bg-slate-100 font-medium text-sm transition-all">Отмена</button>
                    <button type="submit" class="px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-medium text-sm shadow-sm transition-all">Создать</button>
                </div>
            </form>
        </div>
    </div>

    <div id="month-calendar-modal" class="fixed inset-0 bg-slate-900/40 backdrop-blur-sm hidden items-center justify-center z-50 p-4">
        <div class="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl border border-slate-100">
            <div class="flex justify-between items-center mb-4">
                <h3 id="month-calendar-title" class="text-lg font-bold text-slate-900">Календарь месяца</h3>
                <button onclick="closeMonthCalendarModal()" class="text-slate-400 hover:text-slate-600"><i data-lucide="x" class="w-5 h-5"></i></button>
            </div>
            
            <div class="flex items-center justify-between mb-4">
                <button onclick="changeCalendarMonth(-1)" class="p-1 rounded-full border border-slate-200 hover:bg-slate-50 text-slate-600 transition-all"><i data-lucide="chevron-left" class="w-5 h-5"></i></button>
                <span id="calendar-month-label" class="font-bold text-slate-700 text-sm"></span>
                <button onclick="changeCalendarMonth(1)" class="p-1 rounded-full border border-slate-200 hover:bg-slate-50 text-slate-600 transition-all"><i data-lucide="chevron-right" class="w-5 h-5"></i></button>
            </div>

            <div class="grid grid-cols-7 gap-1 text-center text-[10px] font-bold text-slate-400 uppercase mb-2">
                <span>Пн</span><span>Вт</span><span>Ср</span><span>Чт</span><span>Пт</span><span>Сб</span><span>Вс</span>
            </div>
            
            <div id="calendar-days-grid" class="grid grid-cols-7 gap-1"></div>
        </div>
    </div>

    <!-- Системные алерты/конфирмы -->
    <div id="confirm-modal" class="fixed inset-0 bg-slate-900/40 backdrop-blur-sm hidden items-center justify-center z-[60] p-4">
        <div class="bg-white rounded-2xl max-w-sm w-full p-6 shadow-xl border border-slate-100 flex flex-col items-center text-center">
            <div class="w-12 h-12 rounded-full bg-rose-50 text-rose-600 flex items-center justify-center mb-4">
                <i data-lucide="alert-triangle" class="w-6 h-6"></i>
            </div>
            <h4 id="confirm-title" class="font-bold text-slate-950 text-lg mb-2">Вы уверены?</h4>
            <p id="confirm-text" class="text-sm text-slate-500 mb-6"></p>
            <div class="flex gap-2 w-full">
                <button id="confirm-no-btn" class="flex-1 py-2 px-4 rounded-xl border border-slate-200 hover:bg-slate-50 text-slate-600 font-semibold text-sm transition-all">Отмена</button>
                <button id="confirm-yes-btn" class="flex-1 py-2 px-4 rounded-xl bg-rose-600 hover:bg-rose-700 text-white font-semibold text-sm transition-all">Подтвердить</button>
            </div>
        </div>
    </div>

    <button id="back-to-current-week-btn" onclick="goToCurrentWeek()" class="fixed bottom-6 left-1/2 -translate-x-1/2 bg-indigo-600 hover:bg-indigo-700 text-white px-5 py-3 rounded-full shadow-lg flex items-center gap-2 text-sm font-semibold transition-all z-30 hidden scale-100 hover:scale-105">
        <i data-lucide="rotate-ccw" class="w-4 h-4"></i> Вернуться к текущей неделе
    </button>

    <div id="toast-container" class="fixed bottom-4 right-4 z-50 flex flex-col gap-2"></div>

    <script>
        let state = {
            siteTitle: "Ежедневничек",
            motivationalImage: "",
            bannerX: 0,
            bannerY: 0,
            bannerScale: 1.0,
            categories: [],
            tasks: [],
            goals: [],
            notesList: [],
            currentSort: "manual"
        };

        let currentTab = 'main';
        let currentWeekOffset = 0;
        let calendarActiveDate = new Date();
        let isPanningBanner = false;
        let startPanX = 0, startPanY = 0;
        let basePanX = 0, basePanY = 0;

        let currentSelectedImage = null;
        let currentRightClickedImage = null;
        let copiedImageBase64 = null;
        let copiedImageStyle = "";

        const now = new Date();
        const today_str = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
        const tom = new Date(now.getTime() + 24 * 60 * 60 * 1000);
        const tomorrow_str = `${tom.getFullYear()}-${String(tom.getMonth() + 1).padStart(2, '0')}-${String(tom.getDate()).padStart(2, '0')}`;

        function showNotification(text, type = "success") {
            const container = document.getElementById('toast-container');
            const toast = document.createElement('div');
            toast.className = `flex items-center gap-2 p-4 rounded-xl text-white font-semibold text-sm shadow-lg transform translate-y-2 opacity-0 transition-all duration-300 ${type === 'error' ? 'bg-rose-500' : 'bg-slate-800'}`;
            toast.innerHTML = `<i data-lucide="${type === 'error' ? 'alert-circle' : 'check'}" class="w-4 h-4"></i><span>${text}</span>`;
            container.appendChild(toast);
            lucide.createIcons();
            setTimeout(() => { toast.classList.remove('translate-y-2', 'opacity-0'); }, 10);
            setTimeout(() => {
                toast.classList.add('translate-y-2', 'opacity-0');
                setTimeout(() => toast.remove(), 300);
            }, 3000);
        }

        function customConfirm(title, text, onConfirm) {
            const modal = document.getElementById('confirm-modal');
            document.getElementById('confirm-title').innerText = title;
            document.getElementById('confirm-text').innerText = text;
            modal.classList.remove('hidden');
            modal.classList.add('flex');
            
            document.getElementById('confirm-yes-btn').onclick = function() {
                modal.classList.add('hidden');
                modal.classList.remove('flex');
                onConfirm();
            };
            document.getElementById('confirm-no-btn').onclick = function() {
                modal.classList.add('hidden');
                modal.classList.remove('flex');
            };
        }

        function switchTab(tabName) {
            currentTab = tabName;
            const tabs = ['main', 'goals', 'notes'];
            tabs.forEach(t => {
                document.getElementById(`view-${t}`).classList.add('hidden');
                document.getElementById(`tab-${t}-btn`).className = "flex items-center gap-4 py-3 px-3.5 rounded-xl hover:bg-slate-800 text-slate-300 hover:text-white transition-all w-full text-left";
            });

            document.getElementById(`view-${tabName}`).classList.remove('hidden');
            const activeBtn = document.getElementById(`tab-${tabName}-btn`);
            activeBtn.className = "flex items-center gap-4 py-3 px-3.5 rounded-xl bg-slate-800 text-white transition-all w-full text-left";

            if (tabName === 'main') {
                document.getElementById('header-actions').classList.remove('hidden');
                renderDays();
            } else {
                document.getElementById('header-actions').classList.add('hidden');
                if (tabName === 'goals') renderGoals();
                else if (tabName === 'notes') renderNotesStack();
            }
        }

        function dragTask(ev, taskId) {
            ev.dataTransfer.setData("text/plain", taskId);
            ev.currentTarget.classList.add('opacity-40');
        }

        function dragEndTask(ev) {
            ev.currentTarget.classList.remove('opacity-40');
        }

        function allowDrop(ev) {
            ev.preventDefault();
        }

        function dragOverDay(ev, el) {
            ev.preventDefault();
            el.classList.add('bg-indigo-50/40', 'border-indigo-300');
        }

        function dragLeaveDay(ev, el) {
            el.classList.remove('bg-indigo-50/40', 'border-indigo-300');
        }

        function dropTask(ev, dateKey, el) {
            ev.preventDefault();
            el.classList.remove('bg-indigo-50/40', 'border-indigo-300');
            const taskId = ev.dataTransfer.getData("text/plain");
            const task = state.tasks.find(t => t.id === taskId);
            if (task) {
                task.date = dateKey;
                renderDays();
                saveStateToServer(false);
                showNotification("Задача перенесена");
            }
        }

        // Перетаскивание целей
        let draggedGoalId = null;

        function allowGoalDrop(ev) {
            ev.preventDefault();
        }

        function dragGoalStart(e, id) {
            draggedGoalId = id;
            e.dataTransfer.effectAllowed = 'move';
            e.dataTransfer.setData("text/plain", id);
            e.currentTarget.classList.add('opacity-40');
        }

        function dragGoalEnd(e) {
            e.currentTarget.classList.remove('opacity-40');
        }

        function dragOverGoal(e, el) {
            e.preventDefault();
            el.classList.add('drag-over-goal');
        }

        function dragLeaveGoal(e, el) {
            el.classList.remove('drag-over-goal');
        }

        function dropGoal(e, targetId, el) {
            e.preventDefault();
            el.classList.remove('drag-over-goal');
            const sourceId = draggedGoalId || e.dataTransfer.getData("text/plain");
            if (sourceId && sourceId !== targetId) {
                const sourceIndex = state.goals.findIndex(g => g.id === sourceId);
                const targetIndex = state.goals.findIndex(g => g.id === targetId);
                if (sourceIndex > -1 && targetIndex > -1) {
                    const [removed] = state.goals.splice(sourceIndex, 1);
                    state.goals.splice(targetIndex, 0, removed);
                    state.currentSort = "manual";
                    document.getElementById('sort-label-text').innerText = "Сортировка: Произвольно";
                    renderGoals();
                    saveStateToServer(false);
                }
            }
            draggedGoalId = null;
        }

        async function fetchPlannerData() {
            try {
                const response = await fetch('/api/data');
                state = await response.json();
                renderAll();
            } catch (err) {
                console.error("Ошибка при получении данных:", err);
            }
        }

        async function saveStateToServer(shouldRenderAll = true) {
            try {
                await fetch('/api/save', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(state)
                });
                if (shouldRenderAll) {
                    renderAll();
                }
            } catch (err) {
                console.error("Ошибка при сохранении данных:", err);
            }
        }

        function getMondayOfWeek(offset) {
            const today = new Date();
            const monday = new Date(today.getFullYear(), today.getMonth(), today.getDate(), 12, 0, 0, 0);
            const day = monday.getDay();
            const diff = monday.getDate() - day + (day === 0 ? -6 : 1) + (offset * 7);
            return new Date(monday.getFullYear(), monday.getMonth(), diff, 12, 0, 0, 0);
        }

        function goToCurrentWeek() {
            currentWeekOffset = 0;
            renderDays();
        }

        function clampBanner(W, H, img, scale, x, y) {
            const imgAspect = img.naturalWidth / img.naturalHeight;
            const frameAspect = W / H;
            let baseW, baseH;
            
            if (imgAspect > frameAspect) {
                baseH = H;
                baseW = H * imgAspect;
            } else {
                baseW = W;
                baseH = W / imgAspect;
            }

            const minScaleX = W / baseW;
            const minScaleY = H / baseH;
            const minScale = Math.max(minScaleX, minScaleY, 1.0);
            if (scale < minScale) scale = minScale;

            const maxTranslateX = Math.max(0, (baseW * scale - W) / 2);
            const maxTranslateY = Math.max(0, (baseH * scale - H) / 2);

            if (x > maxTranslateX) x = maxTranslateX;
            if (x < -maxTranslateX) x = -maxTranslateX;
            if (y > maxTranslateY) y = maxTranslateY;
            if (y < -maxTranslateY) y = -maxTranslateY;

            return { scale, x, y };
        }

        function triggerBannerUpload() {
            document.getElementById('banner-file-input').click();
        }

        function uploadBanner(e) {
            const file = e.target.files[0];
            if (!file) return;
            const reader = new FileReader();
            reader.onload = function(evt) {
                state.motivationalImage = evt.target.result;
                state.bannerX = 0;
                state.bannerY = 0;
                state.bannerScale = 1.0;
                saveStateToServer(true);
                showNotification("Изображение добавлено. Вы можете двигать и зумить его!");
            };
            reader.readAsDataURL(file);
        }

        function removeBanner() {
            customConfirm("Удалить баннер", "Вы действительно хотите убрать мотивирующее изображение?", () => {
                state.motivationalImage = "";
                saveStateToServer(true);
                showNotification("Изображение удалено");
            });
        }

        function renderAll() {
            document.getElementById('site-title').innerText = state.siteTitle;
            renderBannerOnly();
            
            if (currentTab === 'main') {
                renderDays();
            } else if (currentTab === 'goals') {
                renderGoals();
            } else if (currentTab === 'notes') {
                renderNotesStack();
            }
        }

        function renderBannerOnly() {
            const bannerContainer = document.getElementById('motivational-banner');
            if (state.motivationalImage) {
                bannerContainer.innerHTML = `
                    <div id="banner-frame" class="w-full h-48 md:h-64 rounded-2xl overflow-hidden relative shadow-sm group select-none bg-slate-100">
                        <img id="banner-img" src="${state.motivationalImage}" class="absolute cursor-grab origin-center transition-transform duration-75 select-none pointer-events-none" style="left: 50%; top: 50%; transform: translate(-50%, -50%) translate(${state.bannerX}px, ${state.bannerY}px) scale(${state.bannerScale});">
                        <div class="absolute inset-0 bg-slate-900/20 opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-center justify-end p-4 gap-3">
                            <button onclick="triggerBannerUpload()" class="bg-white/95 hover:bg-white text-slate-800 px-4 py-2 rounded-xl text-xs font-semibold shadow flex items-center gap-1.5 transition-all">
                                <i data-lucide="image-plus" class="w-4 h-4"></i> Изменить
                            </button>
                            <button onclick="removeBanner()" class="bg-rose-600 hover:bg-rose-700 text-white px-4 py-2 rounded-xl text-xs font-semibold shadow flex items-center gap-1.5 transition-all">
                                <i data-lucide="trash-2" class="w-4 h-4"></i> Удалить
                            </button>
                        </div>
                    </div>
                `;
                setupBannerInteractions();
            } else {
                bannerContainer.innerHTML = `
                    <div onclick="triggerBannerUpload()" class="border-2 border-dashed border-slate-200 rounded-2xl h-36 flex flex-col items-center justify-center cursor-pointer hover:border-indigo-400 hover:bg-indigo-50/10 transition-all text-slate-400 group">
                        <div class="p-2 bg-indigo-50 text-indigo-600 rounded-full mb-2 group-hover:scale-110 transition-transform">
                            <i data-lucide="plus" class="w-6 h-6"></i>
                        </div>
                        <span class="text-sm font-semibold text-slate-600">Нажмите, чтобы добавить мотивирующее изображение</span>
                    </div>
                `;
            }
            lucide.createIcons();
        }

        function renderDays() {
            const backBtn = document.getElementById('back-to-current-week-btn');
            if (currentWeekOffset !== 0) {
                backBtn.classList.remove('hidden');
            } else {
                backBtn.classList.add('hidden');
            }

            const monday = getMondayOfWeek(currentWeekOffset);
            const endOfWeek = new Date(monday.getFullYear(), monday.getMonth(), monday.getDate() + 6, 12, 0, 0, 0);
            
            const options = { month: 'long', day: 'numeric' };
            const startLabel = monday.toLocaleDateString('ru-RU', options);
            const endLabel = endOfWeek.toLocaleDateString('ru-RU', options);
            document.querySelector('#current-week-label span').innerText = `${startLabel} — ${endLabel}`;

            const daysContainer = document.getElementById('days-container');
            daysContainer.innerHTML = '';

            const dayNames = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье'];

            for (let i = 0; i < 7; i++) {
                const currentDay = new Date(monday.getFullYear(), monday.getMonth(), monday.getDate() + i, 12, 0, 0, 0);
                
                const year = currentDay.getFullYear();
                const month = String(currentDay.getMonth() + 1).padStart(2, '0');
                const day = String(currentDay.getDate()).padStart(2, '0');
                const dateKey = `${year}-${month}-${day}`;

                const monthsRu = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря'];
                const formattedDateStr = `${currentDay.getDate()} ${monthsRu[currentDay.getMonth()]} ${year % 100}, ${dayNames[i]}`;

                const dayTasks = state.tasks.filter(t => t.date === dateKey);
                const isToday = new Date().toDateString() === currentDay.toDateString();

                const colHTML = `
                    <div 
                        class="bg-white rounded-2xl border ${isToday ? 'border-indigo-400 ring-4 ring-indigo-50' : 'border-slate-200'} shadow-sm flex flex-col overflow-hidden min-h-[440px] transition-all"
                        ondragover="allowDrop(event)"
                        ondragenter="dragOverDay(event, this)"
                        ondragleave="dragLeaveDay(event, this)"
                        ondrop="dropTask(event, '${dateKey}', this)"
                    >
                        <div class="p-3 border-b border-slate-100 flex justify-between items-start ${isToday ? 'bg-indigo-50/30' : 'bg-slate-50/30'}">
                            <div class="overflow-hidden">
                                <h4 class="font-bold text-slate-800 text-xs tracking-tight whitespace-normal leading-tight" title="${formattedDateStr}">${formattedDateStr}</h4>
                                ${isToday ? '<span class="text-[9px] bg-indigo-600 text-white font-semibold px-2 py-0.5 rounded-full mt-1 inline-block uppercase">Сегодня</span>' : ''}
                            </div>
                            <button onclick="openAddTaskModal('${dateKey}')" class="p-1 rounded-lg bg-white border border-slate-200 text-indigo-600 hover:bg-indigo-50 hover:border-indigo-300 transition-all flex items-center justify-center shadow-sm shrink-0" title="Добавить задачу">
                                <i data-lucide="plus" class="w-3.5 h-3.5"></i>
                            </button>
                        </div>
                        
                        <div class="p-2 flex-grow space-y-1.5 max-h-[550px] overflow-y-auto select-none">
                            ${dayTasks.length === 0 ? `
                                <div class="text-center py-20 text-slate-300 text-xs">
                                    <i data-lucide="inbox" class="w-6 h-6 mx-auto mb-1 opacity-40"></i>
                                    Нет дел
                                </div>
                            ` : dayTasks.map(task => {
                                const taskCatsHtml = (task.categories || []).map(catName => {
                                    const catObj = state.categories.find(c => c.name === catName);
                                    const bgClr = catObj ? catObj.color : '#6366f1';
                                    return `
                                        <span class="inline-flex items-center px-1.5 py-0.5 rounded-md text-[9px] font-bold" style="background-color: ${bgClr}20; color: ${bgClr}">
                                            ${escapeHTML(catName)}
                                        </span>
                                    `;
                                }).join(' ');

                                let deadlineHtml = '';
                                if (task.deadlineDate) {
                                    let displayDateStr = '';
                                    if (task.deadlineDate === today_str) {
                                        displayDateStr = '<b>сегодня</b>';
                                    } else if (task.deadlineDate === tomorrow_str) {
                                        displayDateStr = '<b>завтра</b>';
                                    } else {
                                        const d = new Date(task.deadlineDate);
                                        displayDateStr = d.toLocaleDateString('ru-RU', { month: 'short', day: 'numeric' });
                                    }
                                    const timeStr = task.deadlineTime ? `, до ${task.deadlineTime}` : '';
                                    
                                    const isOverdue = !task.completed && task.deadlineDate && new Date(task.deadlineDate + 'T23:59:59') < new Date();
                                    const deadlineColor = isOverdue ? 'text-rose-500 font-bold' : 'text-slate-400 font-medium';

                                    deadlineHtml = `
                                        <div class="flex items-center gap-1 text-[10px] ${deadlineColor} mt-1">
                                            <i data-lucide="clock" class="w-3 h-3"></i>
                                            <span>Срок: ${displayDateStr}${timeStr}</span>
                                        </div>
                                    `;
                                }

                                return `
                                    <div 
                                        draggable="true"
                                        ondragstart="dragTask(event, '${task.id}')"
                                        ondragend="dragEndTask(event)"
                                        class="group relative flex flex-col p-2.5 rounded-xl border ${task.completed ? 'bg-slate-50 border-slate-200' : 'bg-white border-slate-150 shadow-sm hover:border-slate-300'} transition-all gap-1 cursor-grab active:cursor-grabbing"
                                    >
                                        <div class="flex items-start gap-2 pr-14">
                                            <input type="checkbox" ${task.completed ? 'checked' : ''} 
                                                onclick="toggleTaskComplete('${task.id}')" 
                                                class="shrink-0 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500/30 w-4 h-4 cursor-pointer mt-0.5">
                                            
                                            <span class="text-xs font-semibold text-slate-700 whitespace-normal break-words w-full select-text ${task.completed ? 'line-through text-slate-400' : ''}">
                                                ${escapeHTML(task.text)}
                                            </span>
                                        </div>
                                        
                                        ${task.categories && task.categories.length > 0 ? `
                                            <div class="flex flex-wrap gap-1 mt-1 pl-6">
                                                ${taskCatsHtml}
                                            </div>
                                        ` : ''}

                                        ${deadlineHtml ? `<div class="pl-6">${deadlineHtml}</div>` : ''}

                                        <div class="absolute right-1 top-1.5 flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity bg-white/95 py-0.5 px-1 rounded-lg border border-slate-100 shadow-sm">
                                            <button onclick="openEditTaskModal('${task.id}')" class="p-1 hover:text-indigo-600 text-slate-400 rounded transition-all" title="Изменить">
                                                <i data-lucide="edit-3" class="w-3 h-3"></i>
                                            </button>
                                            <button onclick="deleteTask('${task.id}')" class="p-1 hover:text-rose-600 text-slate-400 rounded transition-all" title="Удалить">
                                                <i data-lucide="trash-2" class="w-3 h-3"></i>
                                            </button>
                                        </div>
                                    </div>
                                `;
                            }).join('')}
                        </div>
                    </div>
                `;
                daysContainer.innerHTML += colHTML;
            }
            lucide.createIcons();
        }

        function setupBannerInteractions() {
            const frame = document.getElementById('banner-frame');
            const img = document.getElementById('banner-img');
            if (!frame || !img) return;

            const updateSizingAndPosition = () => {
                const imgAspect = img.naturalWidth / img.naturalHeight;
                const frameAspect = frame.clientWidth / frame.clientHeight;
                if (imgAspect > frameAspect) {
                    img.style.height = '100%';
                    img.style.width = 'auto';
                } else {
                    img.style.width = '100%';
                    img.style.height = 'auto';
                }
                
                // Исправление Bug 2: Сразу кадрируем и убираем любые белые зазоры по краям
                const W = frame.clientWidth;
                const H = frame.clientHeight;
                const clamped = clampBanner(W, H, img, state.bannerScale || 1.0, state.bannerX || 0, state.bannerY || 0);
                state.bannerScale = clamped.scale;
                state.bannerX = clamped.x;
                state.bannerY = clamped.y;
                img.style.transform = `translate(-50%, -50%) translate(${state.bannerX}px, ${state.bannerY}px) scale(${state.bannerScale})`;
            };

            if (img.complete) {
                updateSizingAndPosition();
            } else {
                img.onload = updateSizingAndPosition;
            }

            frame.addEventListener('mousedown', function(e) {
                if (e.target.closest('button')) return;
                e.preventDefault();
                isPanningBanner = true;
                img.classList.remove('cursor-grab');
                img.classList.add('cursor-grabbing');
                startPanX = e.clientX;
                startPanY = e.clientY;
                basePanX = state.bannerX || 0;
                basePanY = state.bannerY || 0;
            });

            const handleMove = function(e) {
                if (!isPanningBanner) return;
                const dx = e.clientX - startPanX;
                const dy = e.clientY - startPanY;

                const W = frame.clientWidth;
                const H = frame.clientHeight;

                let s = state.bannerScale || 1.0;
                let x = basePanX + dx;
                let y = basePanY + dy;

                const clamped = clampBanner(W, H, img, s, x, y);
                state.bannerX = clamped.x;
                state.bannerY = clamped.y;

                img.style.transform = `translate(-50%, -50%) translate(${state.bannerX}px, ${state.bannerY}px) scale(${state.bannerScale})`;
            };

            const handleUp = function() {
                if (isPanningBanner) {
                    isPanningBanner = false;
                    img.classList.remove('cursor-grabbing');
                    img.classList.add('cursor-grab');
                    saveStateToServer(false);
                }
            };

            window.removeEventListener('mousemove', handleMove);
            window.removeEventListener('mouseup', handleUp);
            window.addEventListener('mousemove', handleMove);
            window.addEventListener('mouseup', handleUp);

            frame.addEventListener('wheel', function(e) {
                e.preventDefault();
                const zoomIntensity = 0.05;
                let s = state.bannerScale || 1.0;
                
                if (e.deltaY < 0) {
                    s += zoomIntensity;
                } else {
                    s -= zoomIntensity;
                }

                const W = frame.clientWidth;
                const H = frame.clientHeight;

                let x = state.bannerX || 0;
                let y = state.bannerY || 0;

                const clamped = clampBanner(W, H, img, s, x, y);
                state.bannerScale = clamped.scale;
                state.bannerX = clamped.x;
                state.bannerY = clamped.y;

                img.style.transform = `translate(-50%, -50%) translate(${state.bannerX}px, ${state.bannerY}px) scale(${state.bannerScale})`;
                
                clearTimeout(window.saveBannerTimeout);
                window.saveBannerTimeout = setTimeout(() => saveStateToServer(false), 500);
            });
        }

        function escapeHTML(str) {
            if (!str) return '';
            return str.replace(/[&<>'"]/g, 
                tag => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[tag] || tag)
            );
        }

        function changeWeek(direction) {
            currentWeekOffset += direction;
            renderDays();
        }

        function openAddTaskModal(dateStr) {
            document.getElementById('modal-title').innerText = "Добавить задачу";
            document.getElementById('modal-task-id').value = "";
            document.getElementById('modal-task-date').value = dateStr;
            document.getElementById('modal-task-text').value = "";
            document.getElementById('modal-task-deadline-date').value = "";
            document.getElementById('modal-task-deadline-time').value = "";
            fillCategorySelector([]);
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
            document.getElementById('modal-task-deadline-date').value = task.deadlineDate || "";
            document.getElementById('modal-task-deadline-time').value = task.deadlineTime || "";
            fillCategorySelector(task.categories || []);
            document.getElementById('task-modal').classList.remove('hidden');
            document.getElementById('task-modal').classList.add('flex');
        }

        function closeTaskModal() {
            document.getElementById('task-modal').classList.remove('flex');
            document.getElementById('task-modal').classList.add('hidden');
        }

        function fillCategorySelector(selectedCategories = []) {
            const container = document.getElementById('modal-categories-list');
            container.innerHTML = '';
            
            if (state.categories.length === 0) {
                container.innerHTML = '<span class="text-xs text-slate-400">Нет категорий. Создайте их в меню категорий.</span>';
                return;
            }

            state.categories.forEach(cat => {
                const isChecked = selectedCategories.includes(cat.name) ? 'checked' : '';
                container.innerHTML += `
                    <label class="flex items-center gap-2 cursor-pointer p-1 rounded-lg hover:bg-slate-50 transition-colors">
                        <input type="checkbox" value="${escapeHTML(cat.name)}" ${isChecked} class="rounded text-indigo-600 focus:ring-indigo-500/30">
                        <span class="w-3.5 h-3.5 rounded-full shrink-0" style="background-color: ${cat.color}"></span>
                        <span class="text-xs font-semibold text-slate-700">${escapeHTML(cat.name)}</span>
                    </label>
                `;
            });
        }

        function saveTaskSubmit(event) {
            event.preventDefault();
            const id = document.getElementById('modal-task-id').value;
            const date = document.getElementById('modal-task-date').value;
            const text = document.getElementById('modal-task-text').value.trim();
            const dlDate = document.getElementById('modal-task-deadline-date').value;
            const dlTime = document.getElementById('modal-task-deadline-time').value;

            const checkedBoxes = document.querySelectorAll('#modal-categories-list input[type="checkbox"]:checked');
            const selectedCategories = Array.from(checkedBoxes).map(cb => cb.value);

            if (!text) return;

            if (id) {
                const task = state.tasks.find(t => t.id === id);
                if (task) {
                    task.text = text;
                    task.categories = selectedCategories;
                    task.deadlineDate = dlDate;
                    task.deadlineTime = dlTime;
                }
                showNotification("Задача обновлена");
            } else {
                const newTask = {
                    id: Date.now().toString(),
                    date: date,
                    text: text,
                    categories: selectedCategories,
                    completed: false,
                    deadlineDate: dlDate,
                    deadlineTime: dlTime
                };
                state.tasks.push(newTask);
                showNotification("Задача добавлена");
            }

            closeTaskModal();
            saveStateToServer(true);
        }

        function toggleTaskComplete(id) {
            const task = state.tasks.find(t => t.id === id);
            if (task) {
                task.completed = !task.completed;
                saveStateToServer(true);
            }
        }

        function deleteTask(id) {
            customConfirm("Удалить задачу", "Вы действительно хотите удалить эту задачу из планировщика?", () => {
                state.tasks = state.tasks.filter(t => t.id !== id);
                showNotification("Задача удалена");
                saveStateToServer(true);
            });
        }

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

            state.categories.forEach((cat) => {
                list.innerHTML += `
                    <div class="flex items-center justify-between bg-slate-50 p-2.5 rounded-xl border border-slate-100">
                        <div class="flex items-center gap-2">
                            <span class="w-4 h-4 rounded-full shadow-inner" style="background-color: ${cat.color}"></span>
                            <span class="font-semibold text-slate-700 text-sm">${escapeHTML(cat.name)}</span>
                        </div>
                        <div class="flex gap-1">
                            <button onclick="openEditCategoryModal('${escapeHTML(cat.name)}')" class="p-1.5 hover:bg-indigo-50 hover:text-indigo-600 text-slate-400 rounded-lg transition-all" title="Изменить">
                                <i data-lucide="edit-3" class="w-4 h-4"></i>
                            </button>
                            <button onclick="deleteCategory('${escapeHTML(cat.name)}')" class="p-1.5 hover:bg-rose-50 hover:text-rose-600 text-slate-400 rounded-lg transition-all" title="Удалить">
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
            const clrInput = document.getElementById('new-category-color');
            const newCatName = input.value.trim();
            if (!newCatName) return;

            if (state.categories.some(c => c.name.toLowerCase() === newCatName.toLowerCase())) {
                showNotification("Категория уже существует!", "error");
                return;
            }

            state.categories.push({
                name: newCatName,
                color: clrInput.value
            });
            input.value = "";
            clrInput.value = "#6366f1";
            renderCategoriesList();
            showNotification("Категория добавлена");
            saveStateToServer(true);
        }

        function openEditCategoryModal(name) {
            const cat = state.categories.find(c => c.name === name);
            if (!cat) return;

            document.getElementById('edit-category-old-name').value = cat.name;
            document.getElementById('edit-category-name-input').value = cat.name;
            document.getElementById('edit-category-color-input').value = cat.color;

            document.getElementById('edit-category-modal').classList.remove('hidden');
            document.getElementById('edit-category-modal').classList.add('flex');
        }

        function closeEditCategoryModal() {
            document.getElementById('edit-category-modal').classList.remove('flex');
            document.getElementById('edit-category-modal').classList.add('hidden');
        }

        function saveCategoryEdit() {
            const oldName = document.getElementById('edit-category-old-name').value;
            const newName = document.getElementById('edit-category-name-input').value.trim();
            const newColor = document.getElementById('edit-category-color-input').value;

            if (!newName) return;

            if (oldName !== newName && state.categories.some(c => c.name.toLowerCase() === newName.toLowerCase())) {
                showNotification("Категория с таким названием уже существует!", "error");
                return;
            }

            const cat = state.categories.find(c => c.name === oldName);
            if (cat) {
                cat.name = newName;
                cat.color = newColor;
            }

            state.tasks.forEach(t => {
                if (t.categories && t.categories.includes(oldName)) {
                    t.categories = t.categories.map(c => c === oldName ? newName : c);
                }
            });

            closeEditCategoryModal();
            renderCategoriesList();
            showNotification("Категория сохранена");
            saveStateToServer(true);
        }

        function deleteCategory(catName) {
            customConfirm("Удалить категорию", `Вы действительно хотите удалить категорию "${catName}"? Это очистит её у всех связанных задач.`, () => {
                state.categories = state.categories.filter(c => c.name !== catName);
                state.tasks.forEach(t => {
                    if (t.categories) {
                        t.categories = t.categories.filter(c => c !== catName);
                    }
                });
                renderCategoriesList();
                showNotification("Категория удалена");
                saveStateToServer(true);
            });
        }

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
            if (!newTitle) {
                showNotification("Заголовок не может быть пустым", "error");
                return;
            }

            state.siteTitle = newTitle;
            closeTitleModal();
            showNotification("Заголовок обновлен");
            saveStateToServer(true);
        }

        function openAddGoalModal() {
            document.getElementById('modal-goal-name').value = "";
            document.getElementById('goal-modal').classList.remove('hidden');
            document.getElementById('goal-modal').classList.add('flex');
        }

        function closeGoalModal() {
            document.getElementById('goal-modal').classList.remove('flex');
            document.getElementById('goal-modal').classList.add('hidden');
        }

        function saveGoalSubmit(event) {
            event.preventDefault();
            const name = document.getElementById('modal-goal-name').value.trim();
            if (!name) return;

            const newGoal = {
                id: 'g' + Date.now(),
                name: name,
                addedDate: Date.now(),
                checklist: []
            };

            state.goals.push(newGoal);
            closeGoalModal();
            showNotification("Цель успешно создана");
            saveStateToServer(true);
        }

        function deleteGoal(goalId) {
            customConfirm("Удалить цель", "Вы действительно хотите удалить эту цель и её чек-лист?", () => {
                state.goals = state.goals.filter(g => g.id !== goalId);
                showNotification("Цель удалена");
                saveStateToServer(true);
            });
        }

        function addSubtask(goalId) {
            const input = document.getElementById(`new-subtask-input-${goalId}`);
            const text = input.value.trim();
            if (!text) return;

            const goal = state.goals.find(g => g.id === goalId);
            if (goal) {
                goal.checklist.push({
                    id: 'sub' + Date.now(),
                    text: text,
                    completed: false
                });
                input.value = "";
                saveStateToServer(true);
                showNotification("Пункт добавлен");
            }
        }

        function toggleSubtask(goalId, subtaskId) {
            const goal = state.goals.find(g => g.id === goalId);
            if (goal) {
                const sub = goal.checklist.find(s => s.id === subtaskId);
                if (sub) {
                    sub.completed = !sub.completed;
                    saveStateToServer(true);
                }
            }
        }

        function deleteSubtask(goalId, subtaskId) {
            const goal = state.goals.find(g => g.id === goalId);
            if (goal) {
                goal.checklist = goal.checklist.filter(s => s.id !== subtaskId);
                saveStateToServer(true);
                showNotification("Пункт удален");
            }
        }

        let alphabetSortAsc = true;
        let dateSortAsc = true;
        let progressSortAsc = true;

        function setGoalsSort(type) {
            if (type === 'alphabet') {
                state.currentSort = alphabetSortAsc ? 'alphabet-asc' : 'alphabet-desc';
                alphabetSortAsc = !alphabetSortAsc;
                document.getElementById('sort-label-text').innerText = "Сортировка: " + (state.currentSort === 'alphabet-asc' ? "По алфавиту (А-Я)" : "По алфавиту (Я-А)");
            } else if (type === 'date') {
                state.currentSort = dateSortAsc ? 'date-asc' : 'date-desc';
                dateSortAsc = !dateSortAsc;
                document.getElementById('sort-label-text').innerText = "Сортировка: " + (state.currentSort === 'date-asc' ? "Сначала старые" : "Сначала новые");
            } else if (type === 'progress') {
                state.currentSort = progressSortAsc ? 'progress-asc' : 'progress-desc';
                progressSortAsc = !progressSortAsc;
                document.getElementById('sort-label-text').innerText = "Сортировка: " + (state.currentSort === 'progress-asc' ? "По прогрессу (0%-100%)" : "По прогрессу (100%-0%)");
            } else {
                state.currentSort = 'manual';
                document.getElementById('sort-label-text').innerText = "Сортировка: Произвольно";
            }
            renderGoals();
        }

        function getGoalProgress(goal) {
            const total = goal.checklist.length;
            if (total === 0) return 0;
            const completed = goal.checklist.filter(s => s.completed).length;
            return Math.round((completed / total) * 100);
        }

        function renderGoals() {
            const container = document.getElementById('goals-container');
            container.innerHTML = '';

            if (state.goals.length === 0) {
                container.innerHTML = `
                    <div class="col-span-full bg-slate-50 border border-slate-200 border-dashed rounded-2xl p-12 text-center text-slate-400">
                        <i data-lucide="target" class="w-12 h-12 mx-auto mb-3 opacity-30 text-amber-500"></i>
                        <p class="font-semibold text-sm">У вас пока нет активных целей.</p>
                        <p class="text-xs text-slate-400 mt-1">Добавьте цель кнопкой выше, чтобы начать!</p>
                    </div>
                `;
                lucide.createIcons();
                return;
            }

            let sortedGoals = [...state.goals];
            if (state.currentSort === 'alphabet-asc') {
                sortedGoals.sort((a, b) => a.name.localeCompare(b.name));
            } else if (state.currentSort === 'alphabet-desc') {
                sortedGoals.sort((a, b) => b.name.localeCompare(a.name));
            } else if (state.currentSort === 'date-asc') {
                sortedGoals.sort((a, b) => (a.addedDate || 0) - (b.addedDate || 0));
            } else if (state.currentSort === 'date-desc') {
                sortedGoals.sort((a, b) => (b.addedDate || 0) - (a.addedDate || 0));
            } else if (state.currentSort === 'progress-asc') {
                sortedGoals.sort((a, b) => getGoalProgress(a) - getGoalProgress(b));
            } else if (state.currentSort === 'progress-desc') {
                sortedGoals.sort((a, b) => getGoalProgress(b) - getGoalProgress(a));
            }

            sortedGoals.forEach(goal => {
                const total = goal.checklist.length;
                const completed = goal.checklist.filter(s => s.completed).length;
                const percentage = total === 0 ? 0 : Math.round((completed / total) * 100);

                container.innerHTML += `
                    <div 
                        draggable="true"
                        ondragstart="dragGoalStart(event, '${goal.id}')"
                        ondragend="dragGoalEnd(event)"
                        ondragover="allowGoalDrop(event)"
                        ondragenter="dragOverGoal(event, this)"
                        ondragleave="dragLeaveGoal(event, this)"
                        ondrop="dropGoal(event, '${goal.id}', this)"
                        class="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm flex flex-col gap-4 cursor-grab active:cursor-grabbing transition-all duration-150"
                    >
                        <div class="flex justify-between items-start gap-2">
                            <h3 class="font-bold text-slate-800 text-base leading-snug break-words select-text">${escapeHTML(goal.name)}</h3>
                            <button onclick="deleteGoal('${goal.id}')" class="text-slate-400 hover:text-rose-500 p-1 rounded-lg hover:bg-slate-50 shrink-0 transition-colors" draggable="false">
                                <i data-lucide="trash" class="w-4 h-4"></i>
                            </button>
                        </div>

                        <div class="space-y-1">
                            <div class="flex justify-between text-xs font-semibold text-slate-500">
                                <span>Прогресс</span>
                                <span>${percentage}%</span>
                            </div>
                            <div class="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                                <div class="bg-indigo-600 h-full rounded-full transition-all duration-500 ease-out" style="width: ${percentage}%"></div>
                            </div>
                        </div>

                        <div class="space-y-2 flex-grow select-none">
                            <h4 class="text-xs font-bold text-slate-400 uppercase tracking-wide">Чек-лист цели</h4>
                            <div class="space-y-2 max-h-48 overflow-y-auto pr-1">
                                ${goal.checklist.length === 0 ? `
                                    <p class="text-xs text-slate-300 py-2">Список пуст</p>
                                ` : goal.checklist.map(sub => `
                                    <div class="flex items-center justify-between gap-2 p-2 bg-slate-50/50 rounded-lg hover:bg-slate-50 transition-all border border-slate-100 group">
                                        <label class="flex items-center gap-2 cursor-pointer select-none overflow-hidden text-ellipsis w-full">
                                            <input type="checkbox" ${sub.completed ? 'checked' : ''} 
                                                onclick="toggleSubtask('${goal.id}', '${sub.id}')"
                                                draggable="false"
                                                class="rounded border-slate-300 text-indigo-600 w-3.5 h-3.5 shrink-0">
                                            <span class="text-xs font-semibold text-slate-700 whitespace-normal break-all select-text ${sub.completed ? 'line-through text-slate-400' : ''}">${escapeHTML(sub.text)}</span>
                                        </label>
                                        <button onclick="deleteSubtask('${goal.id}', '${sub.id}')" class="opacity-0 group-hover:opacity-100 text-slate-400 hover:text-rose-500 transition-opacity p-0.5" draggable="false">
                                            <i data-lucide="x" class="w-3.5 h-3.5"></i>
                                        </button>
                                    </div>
                                `).join('')}
                            </div>
                        </div>

                        <div class="flex gap-2 pt-2 border-t border-slate-100">
                            <input 
                                type="text" 
                                id="new-subtask-input-${goal.id}" 
                                placeholder="Добавить пункт..." 
                                draggable="false"
                                ondragstart="event.preventDefault(); event.stopPropagation();"
                                onkeydown="if(event.key === 'Enter') addSubtask('${goal.id}')"
                                class="w-full text-xs border border-slate-200 rounded-xl px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 font-semibold"
                            >
                            <button onclick="addSubtask('${goal.id}')" class="bg-indigo-600 hover:bg-indigo-700 text-white px-3 py-2 rounded-xl text-xs font-semibold flex items-center justify-center shrink-0" draggable="false">
                                <i data-lucide="plus" class="w-3.5 h-3.5"></i>
                            </button>
                        </div>
                    </div>
                `;
            });

            lucide.createIcons();
        }

        function renderNotesStack() {
            const stack = document.getElementById('notes-stack');
            stack.innerHTML = '';

            if (state.notesList.length === 0) {
                stack.innerHTML = `
                    <div class="bg-slate-50 border border-slate-200 border-dashed rounded-2xl p-12 text-center text-slate-400">
                        <i data-lucide="file-text" class="w-12 h-12 mx-auto mb-3 opacity-30 text-emerald-500"></i>
                        <p class="font-semibold text-sm">У вас пока нет заметок.</p>
                        <p class="text-xs text-slate-400 mt-1">Добавьте заметку кнопкой выше!</p>
                    </div>
                `;
                lucide.createIcons();
                return;
            }

            state.notesList.forEach(note => {
                stack.innerHTML += `
                    <div class="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden flex flex-col">
                        <div class="bg-slate-50/50 border-b border-slate-100 px-5 py-3.5 flex justify-between items-center gap-4">
                            <div class="flex items-center gap-3 flex-grow">
                                <button onclick="toggleNoteCollapse('${note.id}')" class="text-slate-400 hover:text-slate-600 p-1 rounded-lg hover:bg-slate-100 transition-colors">
                                    <i data-lucide="${note.collapsed ? 'chevron-right' : 'chevron-down'}" class="w-5 h-5"></i>
                                </button>
                                <input 
                                    type="text" 
                                    value="${escapeHTML(note.title)}" 
                                    onchange="saveNoteTitle('${note.id}', this.value)"
                                    class="bg-transparent font-bold text-slate-800 text-sm focus:outline-none focus:bg-white border border-transparent focus:border-slate-200 rounded-lg px-2 py-1 flex-grow"
                                >
                            </div>
                            <div class="flex items-center gap-1 shrink-0">
                                <button onclick="deleteNote('${note.id}')" class="text-slate-400 hover:text-rose-500 p-1.5 rounded-lg hover:bg-rose-50 transition-colors" title="Удалить заметку">
                                    <i data-lucide="trash-2" class="w-4 h-4"></i>
                                </button>
                            </div>
                        </div>

                        <div class="${note.collapsed ? 'hidden' : 'block'} p-6">
                            <div 
                                id="notes-editor-${note.id}" 
                                contenteditable="true" 
                                placeholder="Начните писать свои мысли..." 
                                class="outline-none min-h-[200px] overflow-y-auto prose max-w-none text-slate-800 select-text"
                                oninput="saveNoteContent('${note.id}', this.innerHTML)"
                                onfocus="setActiveEditor('${note.id}')"
                            >${note.content}</div>
                        </div>
                    </div>
                `;
            });

            lucide.createIcons();
            attachNotesImageListeners();
        }

        let activeNoteId = null;
        function setActiveEditor(id) {
            activeNoteId = id;
        }

        function toggleNoteCollapse(noteId) {
            // Исправление Bug 4 & 7: Предотвращаем конфликт с таймерами автосохранения
            clearTimeout(window.saveNotesTimeout);
            const note = state.notesList.find(n => n.id === noteId);
            if (note) {
                note.collapsed = !note.collapsed;
                saveStateToServer(false); // Тихо сохраняем на сервере
                renderNotesStack(); // Быстро перерисовываем
            }
        }

        function addNote() {
            clearTimeout(window.saveNotesTimeout);
            const newNote = {
                id: 'n' + Date.now(),
                title: 'Новая заметка ' + (state.notesList.length + 1),
                content: '<div>Начните писать здесь...</div>',
                collapsed: false
            };
            state.notesList.push(newNote);
            saveStateToServer(true);
            showNotification("Заметка успешно создана");
        }

        function deleteNote(noteId) {
            // Исправление Bug 4 & 7: Отменяем любые автосохранения
            clearTimeout(window.saveNotesTimeout);
            customConfirm("Удалить заметку", "Вы действительно хотите удалить эту заметку?", () => {
                state.notesList = state.notesList.filter(n => n.id !== noteId);
                saveStateToServer(true);
                showNotification("Заметка удалена");
            });
        }

        function saveNoteTitle(noteId, val) {
            const note = state.notesList.find(n => n.id === noteId);
            if (note) {
                note.title = val.trim() || "Без названия";
                saveStateToServer(false);
            }
        }

        function saveNoteContent(noteId, html) {
            const note = state.notesList.find(n => n.id === noteId);
            if (note) {
                note.content = html;
                
                clearTimeout(window.saveNotesTimeout);
                window.saveNotesTimeout = setTimeout(() => {
                    fetch('/api/save', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(state)
                    });
                }, 1000);
            }
        }

        function applyHighlight(color) {
            document.execCommand('backColor', false, color);
            triggerActiveEditorSave();
        }

        function clearHighlight() {
            document.execCommand('backColor', false, 'rgba(0,0,0,0)');
            triggerActiveEditorSave();
        }

        function formatNote(command) {
            document.execCommand(command, false, null);
            triggerActiveEditorSave();
            updateFormattingState();
        }

        function triggerActiveEditorSave() {
            if (activeNoteId) {
                const el = document.getElementById(`notes-editor-${activeNoteId}`);
                if (el) {
                    saveNoteContent(activeNoteId, el.innerHTML);
                }
            }
        }

        function updateFormattingState() {
            const isBold = document.queryCommandState('bold');
            const isItalic = document.queryCommandState('italic');
            const isStrike = document.queryCommandState('strikeThrough');

            const btnBold = document.getElementById('btn-format-bold');
            const btnItalic = document.getElementById('btn-format-italic');
            const btnStrike = document.getElementById('btn-format-strike');

            if (btnBold) {
                if (isBold) {
                    btnBold.className = "p-2 bg-indigo-100 border border-indigo-300 rounded-xl transition-all font-extrabold text-indigo-700 ring-2 ring-indigo-500/20";
                } else {
                    btnBold.className = "p-2 bg-white hover:bg-slate-100 border border-slate-200 rounded-xl transition-all";
                }
            }
            if (btnItalic) {
                if (isItalic) {
                    btnItalic.className = "p-2 bg-indigo-100 border border-indigo-300 rounded-xl transition-all font-extrabold text-indigo-700 ring-2 ring-indigo-500/20";
                } else {
                    btnItalic.className = "p-2 bg-white hover:bg-slate-100 border border-slate-200 rounded-xl transition-all";
                }
            }
            if (btnStrike) {
                if (isStrike) {
                    btnStrike.className = "p-2 bg-indigo-100 border border-indigo-300 rounded-xl transition-all font-extrabold text-indigo-700 ring-2 ring-indigo-500/20";
                } else {
                    btnStrike.className = "p-2 bg-white hover:bg-slate-100 border border-slate-200 rounded-xl transition-all";
                }
            }
        }

        document.addEventListener('selectionchange', updateFormattingState);

        function triggerImageInsert() {
            if (!activeNoteId) {
                showNotification("Кликните в поле редактирования заметки, чтобы указать куда вставить изображение", "error");
                return;
            }
            document.getElementById('note-image-input').click();
        }

        function insertImageInNote(e) {
            const file = e.target.files[0];
            if (!file) return;
            const reader = new FileReader();
            reader.onload = function(evt) {
                // Вставка изображений без рамки по умолчанию
                const imgHtml = `<img src="${evt.target.result}" style="max-width: 50%; height: auto; display: inline-block; margin: 8px; border: none;" class="rounded-xl shadow-sm cursor-pointer hover:scale-[1.01] transition-transform" />`;
                const ed = document.getElementById(`notes-editor-${activeNoteId}`);
                if (ed) {
                    ed.focus();
                    document.execCommand('insertHTML', false, imgHtml);
                    saveNoteContent(activeNoteId, ed.innerHTML);
                    attachNotesImageListeners();
                }
            };
            reader.readAsDataURL(file);
        }

        function attachNotesImageListeners() {
            const imgs = document.querySelectorAll('#notes-stack img');
            imgs.forEach(img => {
                img.onclick = function(e) {
                    e.stopPropagation();
                    selectImage(img);
                };
            });
        }

        function selectImage(img) {
            if (currentSelectedImage) {
                currentSelectedImage.classList.remove('ring-4', 'ring-indigo-600');
            }
            currentSelectedImage = img;
            currentSelectedImage.classList.add('ring-4', 'ring-indigo-600');
            repositionToolbar();
        }

        // Привязка тулбара и контекстного меню к скроллу страницы
        function repositionToolbar() {
            if (!currentSelectedImage) return;
            const rect = currentSelectedImage.getBoundingClientRect();
            const toolbar = document.getElementById('image-toolbar');
            
            toolbar.style.top = `${rect.top + window.scrollY - 50}px`;
            toolbar.style.left = `${rect.left + window.scrollX + (rect.width / 2) - 130}px`;
            toolbar.classList.remove('hidden');
            toolbar.classList.add('flex');
        }

        function hideImageToolbar() {
            const toolbar = document.getElementById('image-toolbar');
            toolbar.classList.add('hidden');
            toolbar.classList.remove('flex');
            if (currentSelectedImage) {
                currentSelectedImage.classList.remove('ring-4', 'ring-indigo-600');
                currentSelectedImage = null;
            }
        }

        document.addEventListener('click', function(e) {
            if (!e.target.closest('#image-toolbar') && !e.target.closest('#notes-stack img')) {
                hideImageToolbar();
            }
            if (!e.target.closest('#image-context-menu')) {
                hideImageContextMenu();
            }
        });

        window.addEventListener('scroll', () => {
            hideImageContextMenu();
            repositionToolbar();
        }, true);

        window.addEventListener('resize', () => {
            repositionToolbar();
        }, true);

        function resizeSelectedImage(factor) {
            if (!currentSelectedImage) return;
            let currentPercent = parseFloat(currentSelectedImage.style.width) || 50;
            let newPercent = Math.min(100, Math.max(10, currentPercent * factor));
            currentSelectedImage.style.width = `${newPercent}%`;
            triggerActiveEditorSave();
            setTimeout(repositionToolbar, 100);
        }

        function setSelectedImagePercent(pct) {
            if (!currentSelectedImage) return;
            currentSelectedImage.style.width = `${pct}%`;
            triggerActiveEditorSave();
            setTimeout(repositionToolbar, 100);
        }

        function deleteSelectedImage() {
            if (!currentSelectedImage) return;
            currentSelectedImage.remove();
            hideImageToolbar();
            triggerActiveEditorSave();
        }

        document.addEventListener('contextmenu', function(e) {
            const img = e.target.closest('#notes-stack img');
            if (img) {
                e.preventDefault();
                currentRightClickedImage = img;
                showImageContextMenu(e.pageX, e.pageY);
            } else {
                hideImageContextMenu();
            }
        });

        function showImageContextMenu(x, y) {
            const menu = document.getElementById('image-context-menu');
            menu.style.top = `${y}px`;
            menu.style.left = `${x}px`;
            menu.classList.remove('hidden');

            const pasteBtn = document.getElementById('ctx-paste-btn');
            if (copiedImageBase64) {
                pasteBtn.classList.remove('opacity-50', 'pointer-events-none');
            } else {
                pasteBtn.classList.add('opacity-50', 'pointer-events-none');
            }
        }

        function hideImageContextMenu() {
            const menu = document.getElementById('image-context-menu');
            menu.classList.add('hidden');
        }

        function imageAction(action) {
            if (!currentRightClickedImage) return;
            hideImageContextMenu();

            if (action === 'align-left') {
                currentRightClickedImage.style.float = 'left';
                currentRightClickedImage.style.display = 'inline-block';
                currentRightClickedImage.style.margin = '8px 16px 8px 0';
                currentRightClickedImage.style.clear = 'none';
            } else if (action === 'align-right') {
                currentRightClickedImage.style.float = 'right';
                currentRightClickedImage.style.display = 'inline-block';
                currentRightClickedImage.style.margin = '8px 0 8px 16px';
                currentRightClickedImage.style.clear = 'none';
            } else if (action === 'align-center') {
                currentRightClickedImage.style.float = 'none';
                currentRightClickedImage.style.display = 'block';
                currentRightClickedImage.style.margin = '16px auto';
                currentRightClickedImage.style.clear = 'both';
            } else if (action === 'copy') {
                copiedImageBase64 = currentRightClickedImage.src;
                copiedImageStyle = currentRightClickedImage.style.cssText;
                showNotification("Изображение скопировано");
            } else if (action === 'cut') {
                copiedImageBase64 = currentRightClickedImage.src;
                copiedImageStyle = currentRightClickedImage.style.cssText;
                currentRightClickedImage.remove();
                triggerActiveEditorSave();
                showNotification("Изображение вырезано");
            } else if (action === 'paste') {
                if (copiedImageBase64 && activeNoteId) {
                    const imgHtml = `<img src="${copiedImageBase64}" style="${copiedImageStyle}" class="rounded-xl shadow-md cursor-pointer hover:scale-[1.01] transition-transform" />`;
                    const ed = document.getElementById(`notes-editor-${activeNoteId}`);
                    if (ed) {
                        ed.focus();
                        document.execCommand('insertHTML', false, imgHtml);
                        saveNoteContent(activeNoteId, ed.innerHTML);
                        attachNotesImageListeners();
                        showNotification("Изображение вставлено");
                    }
                }
            } else if (action === 'border') {
                // Определение наличия границы
                const hasBorder = currentRightClickedImage.style.border && 
                                  currentRightClickedImage.style.border !== 'none' && 
                                  !currentRightClickedImage.style.border.includes('transparent') &&
                                  currentRightClickedImage.style.borderWidth !== '0px';
                if (hasBorder) {
                    currentRightClickedImage.style.border = 'none';
                } else {
                    currentRightClickedImage.style.border = '4px solid #868e96'; 
                }
            } else if (action === 'rotate') {
                let currentRot = parseInt(currentRightClickedImage.getAttribute('data-rotation')) || 0;
                let nextRot = (currentRot + 90) % 360;
                currentRightClickedImage.setAttribute('data-rotation', nextRot);
                currentRightClickedImage.style.transform = `rotate(${nextRot}deg)`;
            } else if (action === 'delete') {
                currentRightClickedImage.remove();
                triggerActiveEditorSave();
                showNotification("Изображение удалено");
            }

            triggerActiveEditorSave();
        }

        function openMonthCalendarModal() {
            calendarActiveDate = new Date();
            renderCalendarGrid();
            document.getElementById('month-calendar-modal').classList.remove('hidden');
            document.getElementById('month-calendar-modal').classList.add('flex');
        }

        function closeMonthCalendarModal() {
            document.getElementById('month-calendar-modal').classList.remove('flex');
            document.getElementById('month-calendar-modal').classList.add('hidden');
        }

        function changeCalendarMonth(direction) {
            calendarActiveDate.setMonth(calendarActiveDate.getMonth() + direction);
            renderCalendarGrid();
        }

        function renderCalendarGrid() {
            const year = calendarActiveDate.getFullYear();
            const month = calendarActiveDate.getMonth();
            
            const monthNamesRu = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'];
            document.getElementById('calendar-month-label').innerText = `${monthNamesRu[month]} ${year}`;

            const grid = document.getElementById('calendar-days-grid');
            grid.innerHTML = '';

            const firstDayIndex = new Date(year, month, 1).getDay();
            const shift = firstDayIndex === 0 ? 6 : firstDayIndex - 1;

            const totalDaysInMonth = new Date(year, month + 1, 0).getDate();
            const totalDaysPrevMonth = new Date(year, month, 0).getDate();

            for (let i = shift; i > 0; i--) {
                const dayNum = totalDaysPrevMonth - i + 1;
                const d = new Date(year, month - 1, dayNum);
                grid.appendChild(createCalendarDayElement(dayNum, d, true));
            }

            for (let i = 1; i <= totalDaysInMonth; i++) {
                const d = new Date(year, month, i);
                grid.appendChild(createCalendarDayElement(i, d, false));
            }

            const remaining = 42 - (shift + totalDaysInMonth);
            for (let i = 1; i <= remaining; i++) {
                const d = new Date(year, month + 1, i);
                grid.appendChild(createCalendarDayElement(i, d, true));
            }
        }

        function createCalendarDayElement(label, date, isNeighborMonth) {
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = `p-2 rounded-xl text-xs font-semibold transition-all hover:bg-indigo-50 hover:text-indigo-600 flex items-center justify-center h-9 w-9 mx-auto ${isNeighborMonth ? 'text-slate-300' : 'text-slate-700 bg-slate-50'}`;
            
            if (date.toDateString() === new Date().toDateString()) {
                btn.className += ' ring-2 ring-indigo-500 ring-offset-1 text-indigo-600 bg-indigo-50';
            }

            btn.innerText = label;
            btn.onclick = () => selectWeekFromCalendar(date);
            return btn;
        }

        function selectWeekFromCalendar(targetDate) {
            const today = new Date();
            today.setHours(12, 0, 0, 0);
            
            const dayOfWeekToday = today.getDay();
            const mondayToday = new Date(today);
            mondayToday.setDate(today.getDate() + (dayOfWeekToday === 0 ? -6 : 1 - dayOfWeekToday));
            mondayToday.setHours(12, 0, 0, 0);

            const dayOfWeekTarget = targetDate.getDay();
            const mondayTarget = new Date(targetDate);
            mondayTarget.setDate(targetDate.getDate() + (dayOfWeekTarget === 0 ? -6 : 1 - dayOfWeekTarget));
            mondayTarget.setHours(12, 0, 0, 0);

            const diffTime = mondayTarget.getTime() - mondayToday.getTime();
            const diffWeeks = Math.round(diffTime / (1000 * 60 * 60 * 24 * 7));

            currentWeekOffset = diffWeeks;
            closeMonthCalendarModal();
            renderDays();
        }

        fetchPlannerData();
    </script>
</body>
</html>
"""

def open_browser():
    time.sleep(1.5)
    webbrowser.open(f"http://localhost:{PORT}")

if __name__ == "__main__":
    threading.Thread(target=open_browser, daemon=True).start()

    print(f"Запускаем оптимизированный сервер на порту {PORT}...")
    print(f"Ссылка: http://localhost:{PORT}")
    
    server_address = ('', PORT)
    httpd = socketserver.TCPServer(server_address, PlannerRequestHandler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nСервер успешно остановлен.")
        sys.exit(0)
