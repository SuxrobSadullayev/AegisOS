<div align="center">

# 🛡️ Aegis AI Operating System

**Production-Grade, AI-Native Operating System & Multi-Agent Execution Framework for Autonomous Coding Agents**

*Interactive REPL Shell · Multi-Agent Event Bus · Process Sandbox Isolation · Supply Chain Security · Epistemic Truth Engine · 12 Quality Gates*

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-2.3.0--production-green.svg)](CHANGELOG.md)
[![Build Status](https://img.shields.io/badge/tests-418%2B%20passed-brightgreen.svg)](runtime/tests/)

🌐 **Languages / Tillar / Языки:**
[🇬🇧 English](#-english) • [🇺🇿 O'zbekcha](#-ozbekcha) • [🇷🇺 Русский](#-русский)

</div>

---

<a name="-english"></a>
# 🇬🇧 English

## 📖 What is Aegis AI OS?

**Aegis AI Operating System** is a secure, interactive, zero-external-dependency AI Operating System designed to coordinate autonomous AI agents, execute LLM coding workflows, and enforce strict security policies.

Unlike traditional wrappers, Aegis operates as a **Layer 0 Kernel Engine** enforcing deterministic execution pipelines, Default DENY permission models, subprocess sandbox isolation, HMAC digital signature verification, multi-agent event bus routing, and epistemic claim validation without modifying model weights.

## ✨ Features & Capabilities

- **🤖 Multi-Agent Orchestration:** Coordinate specialized AI agents over a secure, priority-based event bus with circular delegation protection.
- **⚡ Interactive REPL & CLI:** Terminal chat shell with slash commands (`/status`, `/session`, `/plugins`, `/provider`) and single-shot task execution.
- **🛡️ Process Sandbox Isolation:** Execute third-party plugins and untrusted code in isolated Python worker subprocesses with Default DENY filesystem, network, and subprocess restrictions.
- **📦 Plugin Marketplace & Supply Chain Security:** Package, verify, publish, install, update, and rollback `.aegis-plugin` bundles with SHA-256 integrity hashes and HMAC-SHA256 digital signatures.
- **🌐 Multi-Provider Model Gateway:** Provider routing across **Google Gemini**, **Anthropic Claude**, **OpenAI**, **OpenRouter**, and **Mock** providers with exponential backoff retries and zero secret leakage.
- **🔒 Centralized Secret Redaction:** Guarantees zero secret leakage by masking API keys, JWT tokens, and credentials across logs, error tracebacks, snapshots, and `repr()` strings.
- **🧠 Epistemic Truth Engine:** Verify AI reasoning claims using DAG evidence hierarchies (Level 0–5) and automatic cascade invalidation.
- **📊 Production Observability & Audit:** Structured JSONL logging (`runtime.jsonl`), immutable security audit logging (`audit.jsonl`), and p50/p95/p99 latency telemetry.

## 🚀 Installation & Quick Start

```bash
# 1. Clone the Aegis repository
git clone https://github.com/SuxrobSadullayev/AegisOS.git
cd AegisOS

# 2. Make the aegis CLI executable
chmod +x aegis

# 3. Verify installation
./aegis --version
```

## ⚙️ Configuration & API Keys

Set environment variables for your target LLM provider:

```bash
export GEMINI_API_KEY="your-gemini-api-key"
export ANTHROPIC_API_KEY="your-anthropic-api-key"
export OPENAI_API_KEY="your-openai-api-key"
export OPENROUTER_API_KEY="your-openrouter-api-key"
```

## 🎯 Usage

```bash
# Start interactive REPL shell
./aegis

# Single-shot task execution
./aegis --task "Review Python security architecture"

# Specify provider and reasoning depth
./aegis --task "Optimize C++ memory pool" --provider gemini --reasoning-depth L3
```

## 🧪 Testing

```bash
python3 -m unittest discover -s runtime/tests -p "test_*.py"
```

---

<a name="-ozbekcha"></a>
# 🇺🇿 O'zbekcha

## 📖 Aegis AI OS nima?

**Aegis AI Operating System** — bu avtonom AI agentlarni koordinatsiya qilish, LLM dasturlash vazifalarini bajarish va xavfsizlik siyosatlarini ta'minlash uchun mo'ljallangan, nol tashqi bog'liqlikka (zero external dependencies) ega xavfsiz va interaktiv Operatsion Tizimdir.

Oddiy wrapper'lardan farqli o'laroq, Aegis **Layer 0 Kernel Engine** sifatida ishlaydi. U deterministik ijro konveyerini, Default DENY ruxsat modelini, subprocess sandbox izolatsiyasini, HMAC raqamli imzo tekshiruvini, multi-agent hodisalar shinasini (event bus) hamda gipotezalarni epistematik tasdiqlashni ta'minlaydi.

## ✨ Imkoniyatlar va Xususiyatlar

- **🤖 Multi-Agent Koordinatsiya:** Ixtisoslashgan AI agentlarni ustuvorlikka ega xavfsiz event bus orqali siklik vazifa berishdan himoyalangan holda boshqarish.
- **⚡ Interaktiv REPL va CLI:** Slash buyruqlar (`/status`, `/session`, `/plugins`, `/provider`) va bitta buyruqli task ijrosini qo'llab-quvvatlaydigan terminal chat qobig'i.
- **🛡️ Process Sandbox Izolatsiyasi:** Uchinchi tomon plaginlari va ishonchsiz kodlarni Default DENY fayl tizimi, tarmoq hamda jarayon cheklovlari ostida alohida Python subprocess ishchilarida bajarish.
- **📦 Plugin Marketplace va Ta'minot Zanjiri Xavfsizligi:** `.aegis-plugin` paketlarini SHA-256 va HMAC-SHA256 raqamli imzolari bilan paketlash, tekshirish, o'rnatish, yangilash va rollback qilish.
- **🌐 Ko'p Providerli Model Gateway:** **Google Gemini**, **Anthropic Claude**, **OpenAI**, **OpenRouter** va **Mock** providerlari o'rtasida kalitlar sizib chiqishisiz (zero secret leakage) marshrutlash.
- **🔒 Markazlashtirilgan Maxfiylik Redaksiyasi:** API kalitlar, JWT tokenlar va parollarni loglar, traceback va snapshot'larda avtomatik yopish (`[REDACTED]`).
- **🧠 Epistematik Haqiqat D двигатели (Truth Engine):** AI xulosalarini Level 0–5 dalillar iyerarxiyasi hamda kaskadli bekor qilish orqali tekshirish.
- **📊 Observability va Audit:** Strukturaviy JSONL loglar (`runtime.jsonl`), o'zgartirib bo'lmaydigan xavfsizlik auditi loglari (`audit.jsonl`) hamda latency telemetriyasi.

## 🚀 O'rnatish va Tezkor Boshlash

```bash
# 1. AegisOS repozitoriyasini klonlang
git clone https://github.com/SuxrobSadullayev/AegisOS.git
cd AegisOS

# 2. aegis CLI fayliga ijro ruxsatini bering
chmod +x aegis

# 3. O'rnatishni tekshiring
./aegis --version
```

## ⚙️ Sozlamalar va API Kalitlar

Tanlangan LLM provideri uchun muhit o'zgaruvchilarini o'rnating:

```bash
export GEMINI_API_KEY="sizning-gemini-api-kalitingiz"
export ANTHROPIC_API_KEY="sizning-anthropic-api-kalitingiz"
export OPENAI_API_KEY="sizning-openai-api-kalitingiz"
export OPENROUTER_API_KEY="sizning-openrouter-api-kalitingiz"
```

## 🎯 Foydalanish

```bash
# Interaktiv REPL shell'ni ishga tushirish
./aegis

# Bitta buyruqli vazifani bajarish
./aegis --task "Python xavfsizlik arxitekturasini tahlil qil"

# Provider va fikrlash chuqurligini ko'rsatish
./aegis --task "C++ xotira havzasini optimallashtir" --provider gemini --reasoning-depth L3
```

## 🧪 Testlarni Ishga Tushirish

```bash
python3 -m unittest discover -s runtime/tests -p "test_*.py"
```

---

<a name="-русский"></a>
# 🇷🇺 Русский

## 📖 Что такое Aegis AI OS?

**Aegis AI Operating System** — это безопасная, интерактивная Операционная Система без внешних зависимостей (zero external dependencies), разработанная для координации автономных ИИ-агентов, выполнения задач кодирования LLM и обеспечения строгих политик безопасности.

В отличие от традиционных оберток, Aegis работает как **Ядро Слой 0 (Layer 0 Kernel Engine)**, обеспечивая детерминированные конвейеры выполнения, модель разрешений Default DENY, изоляцию в песочнице изолированных процессов (sandbox), проверку цифровых подписей HMAC, маршрутизацию шины событий мульти-агентов (event bus) и верификацию гипотез.

## ✨ Возможности и Функции

- **🤖 Мульти-Агентная Координация:** Управление специализированными ИИ-агентами через безопасную шину событий с приоритетами и защитой от циклического делегирования.
- **⚡ Интерактивный REPL и CLI:** Терминальный чат-оболочка со слэш-командами (`/status`, `/session`, `/plugins`, `/provider`) и одноразовым выполнением задач.
- **🛡️ Изоляция Процессов в Песочнице (Sandbox):** Выполнение сторонних плагинов и ненадежного кода в изолированных подпроцессах Python с ограничениями файловой системы, сети и процессов по умолчанию (Default DENY).
- **📦 Plugin Marketplace и Безопасность Цепочки Поставок:** Упаковка, проверка, публикация, установка, обновление и откат пакетов `.aegis-plugin` с хешами SHA-256 и цифровыми подписями HMAC-SHA256.
- **🌐 Мульти-Провайдерный Шлюз Моделей:** Маршрутизация запросов между **Google Gemini**, **Anthropic Claude**, **OpenAI**, **OpenRouter** и **Mock** без утечки секретов.
- **🔒 Централизованная Маскировка Секретов:** Гарантия нулевой утечки секретов путем автоматического скрытия API-ключей, токенов JWT и паролей в логах, трассировках и дампах (`[REDACTED]`).
- **🧠 Эпистемический Движок Истины (Truth Engine):** Проверка утверждений ИИ с использованием иерархии доказательств (Уровни 0–5) и автоматической каскадной инвалидацией.
- **📊 Наблюдаемость и Аудит:** Структурированные логи JSONL (`runtime.jsonl`), неизменяемый журнал аудита безопасности (`audit.jsonl`) и телеметрия задержек (p50/p95/p99).

## 🚀 Установка и Быстрый Запуск

```bash
# 1. Клонируйте репозиторий AegisOS
git clone https://github.com/SuxrobSadullayev/AegisOS.git
cd AegisOS

# 2. Сделайте скрипт aegis исполняемым
chmod +x aegis

# 3. Проверьте установку
./aegis --version
```

## ⚙️ Конфигурация и Ключи API

Установите переменные окружения для вашего провайдера LLM:

```bash
export GEMINI_API_KEY="ваш-ключ-gemini-api"
export ANTHROPIC_API_KEY="ваш-ключ-anthropic-api"
export OPENAI_API_KEY="ваш-ключ-openai-api"
export OPENROUTER_API_KEY="ваш-ключ-openrouter-api"
```

## 🎯 Использование

```bash
# Запуск интерактивной оболочки REPL
./aegis

# Одноразовое выполнение задачи
./aegis --task "Проверь архитектуру безопасности Python"

# Указание провайдера и глубины рассуждений
./aegis --task "Оптимизируй пул памяти C++" --provider gemini --reasoning-depth L3
```

## 🧪 Запуск Тестов

```bash
python3 -m unittest discover -s runtime/tests -p "test_*.py"
```

---

## 🏛️ System Architecture Details

```
                                USER REQUEST / REPL CHAT
                                           │
                                           ▼
                                CLI Engine (`./aegis`)
                                           │
                                           ▼
                            Config Precedence Manager
                      (CLI > Env > ~/.aegis/config.yaml > Default)
                                           │
                                           ▼
                            Session Manager (Multi-Turn Memory)
                                           │
                                           ▼
                            Intent Resolver Stage
                                           │
                                           ▼
                            Task Planner Stage ──► Task Coordinator ──► Multi-Agent Event Bus
                                           │
                                           ▼
                            Knowledge Loader Stage
                                           │
                                           ▼
                            Reasoning Engine Stage (L1 / L2 / L3)
                                           │
                                           ▼
                            Truth Engine Stage (Claim DAG)
                                           │
                                           ▼
                            Plugin Hooks & Capability Registry
                                           │
                                           ▼
                            Prompt Composer Stage (Layer 0 Kernel)
                                           │
                                           ▼
                            Model Gateway Stage (Provider Router)
                                           │
                                           ▼
                            Quality Engine Stage (12 Gates)
                                           │
                                           ▼
                            Auto Repair Stage (Max 3 Retries)
                                           │
                                           ▼
                            Session Persistence & Observability Audit
                                           │
                                           ▼
                                FINAL RESPONSE / REPL DISPLAY
```

---

## 📄 License

[MIT License](LICENSE) — free to use, modify, and distribute.
