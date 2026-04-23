# Claude Code Prompt Patch – "Anti-Corner-Cutting"

**Дата первого применения:** 2026-04-10
**Последнее обновление:** 2026-04-10
**Формат документа:** обратный таймлайн — новое вверху, устаревшее/superseded внизу.
**Источник патча:** https://gist.github.com/roman01la/483d1db15043018096ac3babf5688881
**Скрипт:** `patch-claude-code.sh` (Роман Люттиков)

---

## [2026-04-10] Уроки для AI enablement в организациях

*Разбор кейса Claude Code patch + operational harness как иллюстрации зрелого AI tooling.*

### Тезис

**Внедрение AI-ассистента в команду — это не "купили подписку и раздали".** Это появление нового типа компонента в инфраструктуре, у которого есть четыре измерения зрелости, и большинство команд останавливаются на первом.

Этот раздел структурирует эти измерения на конкретном примере Claude Code и может использоваться как teaching material для internal enablement или architecture reviews.

### Четыре измерения зрелости AI-тулинга

| Уровень | Название | Что команда делает | Характерный признак |
|---|---|---|---|
| **0** | **Consumer mode** | Купили подписку, раздали лицензии, используют out-of-the-box | "У нас есть Claude / Copilot / Cursor, все работают" |
| **1** | **Configuration awareness** | Знают что у тулы есть settings, читали доки, меняют базовые параметры (model, temperature, system prompt где доступен) | "Мы настроили промпт под наш стек" |
| **2** | **Behavioral customization** | Понимают что vendor-дефолты оптимизированы не под них, целенаправленно меняют поведение (патчи, кастомные системные промпты, хуки) | "Мы поменяли X чтобы модель перестала Y" |
| **3** | **Operational harness** | Разбираются что тула может сделать на машине / в репо / в сети, явно ограничивают permissions, сетевой доступ, файловый доступ | "У нас allow/deny листы, sandbox, audit log" |
| **4** | **Integrity + lifecycle** | Мониторят что конфиг/патчи не подменили, отслеживают апдейты, имеют процесс реагирования на изменения vendor-дефолтов | "Мы знаем за час если патч слетел или Anthropic что-то поменял" |

**Реальность рынка (оценка, не исследование):** 90%+ команд сидят на уровне 0. 8% — на уровне 1. Остальные 2% — тот уровень где можно говорить про "серьёзный AI enablement".

**Важный nuance:** уровни 3 и 4 нужны **не всем** одинаково. Команде из 5 человек хватит уровня 2. Но как только тула начинает иметь доступ к продакшн-коду, клиентским данным, или агентно что-то автоматизировать в репо — уровни 3–4 становятся обязательными, а не опциональными.

### Измерение 1: Behavioral customization — что вообще можно менять

Клиенты обычно не знают, что в современных AI-тулах можно менять:

- **Системный промпт** — частично через settings/config файлы, частично через патчинг бинаря (как в этом кейсе с `patch-claude-code.sh`)
- **Reasoning budget** — через env vars (`CLAUDE_CODE_DISABLE_ADAPTIVE_THINKING`, `MAX_THINKING_TOKENS`) или effort-настройки
- **Tool permissions** — какие инструменты (Bash, Write, Edit, WebFetch) разрешены агенту и с какими параметрами
- **Model selection** — какая конкретно модель под какие задачи
- **Subagent prompts** — часто у саб-агентов (Explore, Plan, Review) свои системные инструкции, которые тоже можно править
- **Hooks** — пре/пост-команды которые запускаются вокруг действий агента

**Что из этого типично меняют команды уровня 0–1:** только model selection и иногда system prompt (если vendor даёт UI для этого).

**Что упускают:** subagent prompts (огромный эффект на качество), reasoning budget (критично после Feb–Mar 2026 изменений Anthropic), hooks (мощнейший механизм для принудительного поведения).

**Конкретный пример из текущего кейса:** Anthropic в Feb–Mar 2026 тихо поменяли два дефолта (adaptive thinking + effort=medium) и сломали поведение на сложных задачах. Команды уровня 0 это **не заметили даже спустя месяцы** — они думали "что-то модель поглупела, подождём следующий апдейт". Команды уровня 2 обнаружили это за день, нашли воркэраунд, применили через env var и патч. **Разница в ценности тулы между этими двумя уровнями — оценочно 3–5x.**

### Измерение 2: Operational harness — что агент может сделать в твоей среде

Это **самое недооценённое** измерение в командах, и одновременно самое опасное при его отсутствии.

Современный AI-ассистент типа Claude Code / Cursor / Aider имеет на твоей машине:
- Полный shell-доступ (`Bash` tool)
- Read/Write доступ ко всему что доступно твоему user-у
- Сетевой доступ в интернет (WebFetch, WebSearch, curl через Bash)
- Возможность запустить любой устанавливаемый пакет (npm, pip, brew)
- Доступ к env vars, `.env` файлам, `~/.ssh/`, `~/.aws/`, `~/.gnupg/` если ты ему это не запретил явно

**Default настройка большинства команд:** всё разрешено, нет никаких ограничений. Агент может случайно (или при prompt injection из вредоносного репо / issue / README) сделать `rm -rf`, отправить credentials наружу, закоммитить и запушить мусор в main, установить malicious пакет.

**Что такое harness:** декларативное описание того, что агенту **можно** и **нельзя** делать, применяемое на уровне самого инструмента (а не надеждой на "умную модель").

Конкретные механики в Claude Code:
- `permissions.allow` — whitelist команд (префиксы) которые выполняются без подтверждения
- `permissions.deny` — blacklist команд которые **никогда** не выполнятся, даже с подтверждением
- `sandbox.enabled` — изолированная ФС/сеть среда для Bash-команд
- `sandbox.network.allowedDomains` — whitelist доменов для сетевых запросов
- `sandbox.filesystem.denyWrite` — директории куда запрещено писать даже в non-sandbox режиме
- `defaultMode: acceptEdits` — требует явное подтверждение на редактирование файлов

**Команды уровня 0–1 не знают что эти настройки вообще существуют.** Они включают Claude Code, кликают "approve all" и идут дальше.

### Референсный харнесс: рабочий пример (Level 3)

Ниже — структура реального рабочего `~/.claude/settings.json` как пример того, как выглядит Level 3 harness на практике. Конкретные домены и пути адаптируй под стек своей команды. Метапринципы остаются те же.

**1. Permission model — явные whitelist + blacklist:**

- **Allow list** (~40 правил): безопасные git операции (`git status`, `git diff`, `git log`, `git commit`, `git push origin*`), базовый shell (`ls`, `pwd`, `cat`, `head`, `wc`), package managers (`npm install*`, `npm run*`, `pip install*`), GitHub CLI (`gh *`), WebSearch/WebFetch
- **Deny list** (~70 правил) — это где реальная защита:
  - **Destructive ops**: `rm *`, `rmdir*`, `unlink*`, `mv /* *`, `cp /* *`, `dd *`, `mkfs*` — физическое удаление/перезапись блокируется на уровне тулы
  - **Privilege escalation**: `sudo*`, `chmod*`, `chown*`, `launchctl*`, `crontab*` — агент не может менять права или ставить автозагрузки
  - **Destructive git**: `git push --force*`, `git reset --hard*`, `git clean -f*` — защита от потери работы
  - **Remote code execution patterns**: `curl*|*bash*`, `wget*|*sh*`, `eval*`, `exec*`, `source*`, `bash -c*`, `sh -c*` — блокирует классические паттерны RCE через shell
  - **Process control**: `kill*`, `killall*`, `pkill*`
  - **Network tools**: `curl *`, `wget *`, `ssh *`, `scp *`, `nc *`, `ncat *` — принудительно через WebFetch который проходит через sandbox
  - **Python escape hatches**: `python3 -c *import os*`, `python3 -c *subprocess*`, `python3 -c *__import__*`, `python3 -c *import socket*`, `python3 -c *import urllib*`, и ещё ~15 паттернов — блокируют популярные способы обхода через Python one-liners
  - **Clipboard/UI**: `pbcopy*`, `open *` — нельзя утащить данные в буфер обмена или открыть GUI приложения

**2. Network sandbox — explicit allowlist:**

```json
"sandbox": {
  "enabled": true,
  "network": {
    "allowedDomains": [
      "api.anthropic.com",
      "<messaging API под твой стек>",
      "<social/work API под твой стек>",
      "pypi.org",
      "files.pythonhosted.org",
      "registry.npmjs.org"
    ]
  }
}
```

Всего ~6 доменов: API самой модели, пакетные реестры (pypi, npm), и 2–3 под коммуникационные/рабочие интеграции. Агент физически не может обратиться никуда ещё. Это значит:

- Prompt injection через вредоносный README не заставит агента скачать malware — DNS не резолвится
- Credentials не могут быть экспортированы в произвольный collector — сеть не пустит
- Любая новая интеграция (API, MCP сервер) требует явного расширения allowlist — это **trigger для review**, "а зачем агенту нужен этот домен?"

**Принцип отбора доменов:** минимальный набор который позволяет агенту работать над текущим стеком команды. Стартуй с 3-х (API модели + pypi + npm) и расширяй по факту блокировок. Это дешевле чем сразу whitelist-ить десятки доменов "на всякий случай".

**3. Filesystem sandbox:**

```json
"filesystem": {
  "denyWrite": ["/etc", "/System", "/Library"]
}
```

Плюс неявная система allow-within-deny для `~/.claude/settings.json` и других чувствительных точек — sandbox блокирует запись в критичные места даже если Bash команда формально разрешена.

**4. Default mode:**

```json
"defaultMode": "acceptEdits"
```

Значит: агент может редактировать файлы без подтверждения, но Bash команды **не** в allow list всё равно требуют явного approve. Это компромисс между продуктивностью и безопасностью — правки файлов flowят, но любая команда которая может что-то изменить в системе останавливается и ждёт человека.

**5. Single source of truth:**

Всё это в **одном файле** `~/.claude/settings.json`, который версионируется, копируется между машинами, обсуждается как артефакт команды. Не разбросано по env vars, плагинам, keybindings.

### Измерение 3: Integrity + lifecycle (Level 4)

Это то, до чего доходят только самые зрелые команды, и это именно то место где текущий кейс (патчинг `cli.js`) создаёт **новую проблему**.

**Проблема кастомизации:** когда ты пропатчил инструмент (как мы пропатчили Claude Code), пропатченный файл становится **attack target** и **operational debt**:

- **Attack target**: кто-то с code exec правами может заменить патч на что-то вредоносное, и ты не узнаешь пока не начнёт происходить странное. Пропатченный `cli.js` запускается каждый раз когда ты вводишь `claude` — идеальный persistence механизм для атакующего.
- **Operational debt**: патч может слететь от vendor update, от случайного `npm install`, от `brew reinstall`. Без мониторинга ты не узнаешь что твои custom оптимизации перестали работать, и будешь неделями думать "что-то модель опять тупит".

**Что нужно на уровне 4:**

1. **Integrity hashing**: записать SHA256 пропатченного файла сразу после применения
   ```bash
   shasum -a 256 /opt/homebrew/lib/node_modules/@anthropic-ai/claude-code/cli.js \
     > ~/.claude/cli.js.patched.sha256
   ```
   Регулярно проверять `shasum -c` — расхождение = сигнал расследовать

2. **Write protection**: `chmod 444` на критичные скрипты и конфиги, чтобы prompt injection через Edit/Write tool их не перезаписал незаметно
   ```bash
   chmod 444 ~/.claude/patch-claude-code.sh
   ```

3. **Изолированные бэкапы**: копия пропатченного файла **вне** директории где он используется
   ```bash
   cp /opt/homebrew/lib/node_modules/@anthropic-ai/claude-code/cli.js ~/.claude/cli.js.patched-2.1.98.bak
   ```
   Это позволяет сравнивать текущий с бэкапом и детектить подмену

4. **Auto-respond на vendor updates**: watcher (launchd / systemd) который срабатывает когда vendor обновляет бинарь, автоматически переприменяет патчи, логирует действие. В нашем случае — `--watch` режим `patch-claude-code.sh`

5. **Periodic audit**: раз в неделю / месяц — прогонять `--check` режим, читать `~/.claude/patch.log`, проверять хэши. Можно через cron / launchd agent который шлёт уведомление в мессенджер команды

**В референсном примере выше** harness находится на уровне 3, но **до уровня 4 не дотянуто**: integrity hash и `chmod 444` предложены как ручные шаги, watcher не установлен. Это сознательный компромисс — полный level 4 требует дополнительной настройки и добавляет friction при обновлениях.

### Audit questions for AI tooling maturity

Используй эти вопросы на первых звонках, чтобы быстро определить уровень зрелости команды:

**Базовые (Level 0 → 1):**
1. Какие AI-инструменты внедрены в вашем dev-процессе? Кто решил какие?
2. Кто и как настраивал эти инструменты — использовались ли кастомные system prompt / конфиги?
3. Знаете ли вы какая именно модель работает в каждом инструменте прямо сейчас? (многие думают что Claude Code = Opus, хотя там Sonnet по дефолту в ряде режимов)

**Behavioral (Level 1 → 2):**
4. Видели ли вы разницу в поведении инструмента после последних vendor обновлений? Если да — что именно?
5. Есть ли у вас механизм отслеживать когда vendor меняет дефолты? (обычно — нет)
6. Есть ли в вашей команде человек, который **читает release notes** AI-тулов и оценивает impact? (обычно — нет)
7. Пробовали ли вы когда-нибудь патчить/менять системный промпт или reasoning-параметры? Что остановило?

**Operational (Level 2 → 3):**
8. Что ваш AI-ассистент физически может сделать на машине разработчика? Есть ли список? (у 99% команд — нет)
9. Есть ли у вас whitelist команд которые агент может выполнять без подтверждения? (у 99% — нет)
10. Есть ли у вас blacklist команд которые агент не может выполнять **вообще**? (у 99%+ — нет)
11. Ограничен ли сетевой доступ агента? Какие домены ему доступны?
12. Что произойдёт если в README вашего текущего репо появится prompt injection инструктирующий агента экспортировать `.env`? (обычно — ничего не остановит)
13. Какие env-vars / ssh-keys / API tokens доступны агенту прямо сейчас через env?

**Integrity (Level 3 → 4):**
14. Если кто-то подменит конфиг вашего AI-ассистента — через сколько времени вы узнаете?
15. Есть ли у вас integrity-check на критичных AI-файлах (config, patched binaries, MCP servers)?
16. Есть ли у вас immutable бэкапы этих файлов?
17. Куда агент пишет логи? Кто их читает? Есть ли alerting на аномалии?
18. Если vendor завтра изменит дефолт модели — через сколько узнаете и через сколько отреагируете?

Практический эффект этих вопросов: команда, которая уверенно отвечает на 1–3 и начинает мяться на 8+, обычно уже дошла до точки, где нужны permissions, sandboxing, and integrity work — не только prompt tweaks.

### Типовые антипаттерны в командах

Что клиенты обычно делают неправильно, и что на это говорить:

**Антипаттерн 1: "approve all" режим**
Разработчики устают подтверждать каждую команду → переключают в режим "всё разрешено". Пропадает любая защита.
*Что предлагать:* построить allow list для 80% рутинных команд (git, npm, cat, ls), оставить остальное с подтверждением. Быстро, не мешает, не нулевая защита.

**Антипаттерн 2: "один конфиг на всю команду"**
Shared config файл копируется между инженерами без понимания что там. Когда vendor обновляется и ломает что-то — никто не знает что именно сломалось.
*Что предлагать:* конфиг как артефакт, версионируется в отдельном git репо, PR review на изменения, changelog.

**Антипаттерн 3: "мы доверяем Anthropic/OpenAI"**
Команда не читает ToS, не следит за дефолтами, считает что vendor не подложит свинью.
*Что предлагать:* показать кейс Feb–Mar 2026 (Anthropic тихо дропнул effort с high на medium + включил adaptive thinking, что уронило качество). Это не злой умысел, это конфликт метрик vendor vs конечного пользователя. Доверие ≠ отсутствие мониторинга.

**Антипаттерн 4: "AI-инструмент = магия, не инфраструктура"**
Команда трактует Claude Code как что-то между IDE и чатботом, а не как **агента с shell-доступом**. Отсюда — нулевая threat model.
*Что предлагать:* mental model shift — "это не чатбот, это джуниор с sudo правами, который читает каждую строчку что вы ему показываете как инструкцию". Как только это осознано, все остальные вопросы (permissions, sandbox, integrity) начинают иметь смысл.

**Антипаттерн 5: "кастомизация = hacky, лучше не трогать"**
Команда боится патчить/настраивать, потому что "сломается при обновлении" или "вдруг поддержка пошлёт". В итоге сидят на vendor-дефолтах и терпят известные проблемы.
*Что предлагать:* обратная сторона — **отсутствие** кастомизации это тоже решение, только скрытое и без процесса. Легализовать кастомизацию как нормальную практику с lifecycle (патч → тест → мониторинг → реакция на обновления).

---

## [2026-04-10] Персистентность и устойчивость патчей

### Автозапуск при рестарте Mac – НЕ нужен

Патчи прописаны прямо в файл `/opt/homebrew/lib/node_modules/@anthropic-ai/claude-code/cli.js`. Симлинк `~/.local/bin/claude` → этот файл persistent через reboot. **После рестарта Mac всё продолжает работать без действий.**

Watcher (launchd agent) нужен **только** для переживания npm-апдейтов, не для рестартов.

### Что может снести патч

| Событие | Патч слетит? | Автоматическое? |
|---|---|---|
| Рестарт Mac | нет | — |
| `claude update` (native bun) | нет | да (мы не смотрим на native bun) |
| `npm install -g @anthropic-ai/claude-code` | **да** | только если ты запустишь |
| `npm update -g` | **да** | нет, только вручную |
| `brew reinstall --cask claude-code` | нет (если не удалишь `~/.local/bin/claude`) | нет |
| `bash patch-claude-code.sh --restore` | да (явный откат) | нет |
| Удаление `~/.local/bin/claude` | фолбек на cask v2.1.85 | нет |

Реальный риск "само сломается" = один: `npm update -g` когда-нибудь руками запустишь. Решается либо watcher-ом, либо привычкой после апдейта запускать `bash ~/.claude/patch-claude-code.sh` повторно.

### Харденинг (опционально)

**Dumbfuck-защита:**

```bash
# Сделать скрипт патчера read-only чтобы случайно не перезаписать
chmod 444 ~/.claude/patch-claude-code.sh

# Отдельный бэкап пропатченного cli.js вне npm директории
cp /opt/homebrew/lib/node_modules/@anthropic-ai/claude-code/cli.js \
   ~/.claude/cli.js.patched-2.1.98.bak

# Контрольная сумма для проверки integrity потом
shasum -a 256 /opt/homebrew/lib/node_modules/@anthropic-ai/claude-code/cli.js \
  > ~/.claude/cli.js.patched.sha256
```

**Проверка integrity позже:**
```bash
shasum -a 256 -c ~/.claude/cli.js.patched.sha256
# OK = патч цел; FAILED = что-то переписало файл
```

**Attack-защита: реальные ограничения**

Полный attack-proof невозможен без SIP / read-only FS / кодподписи. Патч не расширяет attack surface — любая угроза, которая могла бы компрометировать **непропатченный** `cli.js`, в равной степени компрометирует пропатченный. Но добавляется одна точка: сам скрипт `~/.claude/patch-claude-code.sh`. Его `chmod 444` + хэш cli.js = нормальный baseline.

**Важный нюанс про prompt injection:**

- Bash-tool в Claude Code уважает sandbox deny-рулы (`launchctl *`, `rm *`, `chmod *`, и т.д. из `settings.json`)
- **Edit/Write tool** — **НЕ уважает** sandbox denyWithinAllow, может писать в `~/.claude/settings.json` и `~/.claude/patch-claude-code.sh` без явного approve
- Это значит что теоретически промпт-инъекция (через просмотр вредоносного репо/файла) может подсунуть Claude команду отредактировать эти файлы через Edit-tool
- Защита: `chmod 444` на патч-скрипт (Edit-tool не сможет записать read-only файл), плюс регулярный `shasum -c` чек

### Auto-update patch через watcher (опциональная установка)

Если готов доверять watcher-у авто-перепатчивание при каждом npm-апдейте:

```bash
bash ~/.claude/patch-claude-code.sh --watch
```

Что произойдёт:
- Создастся `~/Library/LaunchAgents/com.user.claude-code-patcher.plist`
- launchd будет следить за `~/.local/share/claude/versions/` (изменения в native bun директории)
- При любом изменении → триггер `patch-claude-code.sh --apply-quiet` → перепатч

**Лог watcher-а:** `~/.claude/patch.log`

**Снять watcher:**
```bash
bash ~/.claude/patch-claude-code.sh --unwatch
```

Или руками:
```bash
launchctl unload ~/Library/LaunchAgents/com.user.claude-code-patcher.plist
rm -f ~/Library/LaunchAgents/com.user.claude-code-patcher.plist
```

**Замечание по безопасности watcher-а:** launchd агент запускает скрипт с твоими uid правами при каждом изменении `versions/` директории. Если кто-то получит write доступ к `patch-claude-code.sh`, он получит code exec при следующем срабатывании триггера. Отсюда — `chmod 444` на скрипт критичнее если ставишь watcher.

---

## [2026-04-10] Parallel Fix #2: Disable Adaptive Thinking

**Источник:** https://reddit.com/r/ClaudeCode/comments/1sfihyr/psa_if_your_opus_is_lobotomized_disable_adaptive/
**Связанная статья:** https://ianlpaterson.com/blog/stop-claude-code-from-lobotomizing-itself-mid-task/

### Контекст проблемы

Anthropic в Feb-Mar 2026 внесли два параллельных изменения, которые вместе уронили качество Claude Code на сложных задачах:

- **9 февраля 2026** – Opus 4.6 + Adaptive Thinking: модель сама решает сколько токенов потратить на "думание" на каждом ходу, вместо фиксированного бюджета `MAX_THINKING_TOKENS`
- **3 марта 2026** – дефолтный effort дропнут с `high` до `medium` (85)

Эффект: на сложных тасках модель "решает" что можно подумать поменьше, срезает углы, галлюцинирует. Комьюнити зовёт это "lobotomized Opus".

### Воркэраунд

Env var `CLAUDE_CODE_DISABLE_ADAPTIVE_THINKING=1` отключает adaptive и возвращает фиксированный бюджет, управляемый `MAX_THINKING_TOKENS`. В сочетании с `"effortLevel": "max"` в settings.json даёт максимально глубокий фиксированный бюджет на каждый ход.

### Example application

Добавлено в `~/.claude/settings.json`:

```json
{
  "effortLevel": "max",
  "env": {
    "CLAUDE_CODE_DISABLE_ADAPTIVE_THINKING": "1"
  }
}
```

### Откат

Удалить блок `env` из `~/.claude/settings.json` или поменять значение на `"0"`.

---

## [2026-04-10] Claude Code Prompt Patch — базовое применение

### Что это и зачем

Claude Code в базовом системном промпте содержит набор инструкций, которые заставляют модель **срезать углы**: приоритезировать краткость ответа над полнотой работы, пропускать error handling, избегать "gold-plating" до степени, когда модель не фиксит даже явно сломанные смежные куски. Роман Люттиков выложил патчер, который точечно переписывает эти 11 строк в `cli.js`, не трогая остальное.

**Классы проблем до патча:**
- "Three similar lines is better than a premature abstraction" → модель оставляет дублирование даже там где оно реально мешает
- "Don't add error handling for scenarios that can't happen" → модель не ставит валидацию даже на реальных границах I/O
- "Your responses should be short and concise" → краткость применяется и к глубине работы, не только к тексту ответа
- "Match the scope of your actions to what was actually requested" → модель не чинит очевидно сломанное рядом с таской
- Subagent-инструкция "fast agent, return quickly" → Explore-агент жертвует полнотой ради скорости

**После патча:** модель по-прежнему лаконична в текстовых ответах, но краткость **отвязана** от качества/полноты работы. Error handling разрешён на реальных границах. Явно сломанное рядом с таской разрешено чинить. Explore-агент делает "thorough" по умолчанию.

### Что именно поменялось (11 патчей)

1. **Output efficiency IMPORTANT line** – убрано "be extra concise", добавлено "do not sacrifice correctness or completeness for simplicity"
2. **Brevity paragraph** – явно зафиксировано что brevity применяется к **сообщениям пользователю**, не к глубине работы
3. **"One sentence" rule** – смягчено, снято с кода и tool calls
4. **Anti-gold-plating** – разрешено чинить сломанное смежное (adjacent broken code)
5. **Skip error handling** – перевёрнуто: "add error handling at real boundaries where failures can realistically occur"
6. **Three-lines rule** – убран хардкор про "дублирование лучше абстракции", заменено на judgment-based
7. **Subagent gold-plate** – усилена полнота: "do the work a careful senior developer would do, including edge cases"
8. **Explore agent speed note** – убрана bias "speed over thoroughness", добавлен triggered thorough mode
9. **Tone "short and concise"** – заменено на "clear and appropriately detailed for complexity"
10. **Subagent code snippet suppression** – разрешено включать релевантные сниппеты в выводы саб-агентов
11. **Match scope instruction** – добавлено "do address closely related issues you discover"

### Как это установлено у Дениса

**Контекст инсталляции (важно):**
- До патча было **три** Claude Code на машине:
  - `/Users/a1/.local/bin/claude` → native installer `~/.local/share/claude/versions/2.1.97` (активный в PATH)
  - `/opt/homebrew/bin/claude` → Homebrew cask `claude-code` v2.1.85 (не активный, но занимал симлинк)
  - npm global – не был установлен
- Homebrew cask блокировал `npm install -g` конфликтом симлинка → пришлось `npm install -g --force @anthropic-ai/claude-code` (перетёрло cask'овский симлинк в `/opt/homebrew/bin/claude`)

**Что в итоге активно:**
- `/Users/a1/.local/bin/claude` → `/opt/homebrew/lib/node_modules/@anthropic-ai/claude-code/cli.js` (пропатченный, v2.1.98)
- Оригинальный непропатченный `cli.js.backup` рядом с ним
- Homebrew cask v2.1.85 лежит мёртвым грузом в `/opt/homebrew/Caskroom/claude-code/`

**Скрипт патчера сохранён в:** `~/.claude/patch-claude-code.sh` (скопирован из `$TMPDIR` в постоянное место).

### Как проверить что патч активен

```bash
# Версия (должна быть npm-овская, не native bun)
claude --version
# → "2.1.98 (Claude Code)"

# Куда ссылается симлинк
readlink /Users/a1/.local/bin/claude
# → /opt/homebrew/lib/node_modules/@anthropic-ai/claude-code/cli.js

# Проверка всех 11 патчей разом
bash ~/.claude/patch-claude-code.sh --check
# → "11 applied, 0 not applied, 0 not found"
```

### Как откатить

**TL;DR команды (copy-paste ready):**
```
To restore: /Users/a1/.claude/patch-claude-code.sh --restore
To remove:  /Users/a1/.claude/patch-claude-code.sh --unwatch
```

#### Полный откат к оригиналу (native bun binary)

```bash
bash ~/.claude/patch-claude-code.sh --restore
```

Что сделает:
1. Восстановит `cli.js` из `cli.js.backup`
2. Перенаправит симлинк `/Users/a1/.local/bin/claude` обратно на native bun-бинарь `~/.local/share/claude/versions/2.1.97` (или на последнюю версию в `versions/`)
3. Удалит watcher если он был установлен

#### Только снять watcher (патч оставить)

```bash
bash ~/.claude/patch-claude-code.sh --unwatch
```

Или ручным путём:
```bash
launchctl unload ~/Library/LaunchAgents/com.user.claude-code-patcher.plist
rm -f ~/Library/LaunchAgents/com.user.claude-code-patcher.plist
```

#### Полная деинсталляция всего npm-трека

```bash
bash ~/.claude/patch-claude-code.sh --restore    # сначала восстановить оригинал симлинка
npm uninstall -g @anthropic-ai/claude-code        # снести npm-пакет
```

#### Если нужен homebrew cask обратно как активный claude

```bash
brew reinstall --cask claude-code
# После этого /opt/homebrew/bin/claude снова будет указывать на cask v2.1.85
# Но PATH всё равно резолвит ~/.local/bin/claude первым — проверь: which claude
```

### Как пережить авто-апдейты (опционально)

Claude Code обновляется сам. Новая версия падает в `~/.local/share/claude/versions/`, но пропатченный `cli.js` при этом не меняется – патчи останутся активны до следующего `npm install -g @anthropic-ai/claude-code` из любого источника.

**Watcher** (macOS launchd агент) следит за `~/.local/share/claude/versions/` и при появлении новой версии:
1. Синхронизирует npm-пакет до той же версии
2. Переприменяет все 11 патчей
3. Переводит симлинк на свежий пропатченный `cli.js`

Установка:
```bash
bash ~/.claude/patch-claude-code.sh --watch
```

Лог watcher-а: `~/.claude/patch.log`

Снять:
```bash
bash ~/.claude/patch-claude-code.sh --unwatch
```

**Важно:** watcher использует `launchctl load`. Если у тебя в `~/.claude/settings.json` `launchctl *` в deny-листе, Claude Code из своей сессии watcher поставить не сможет. Тогда ставь его руками один раз.

### Известные нюансы и гатчи

1. **Homebrew cask конфликт** – если сделать `brew reinstall claude-code`, он перепишет `/opt/homebrew/bin/claude` обратно на v2.1.85 (непропатченную). На активный `~/.local/bin/claude` это не повлияет (PATH резолвит его первым), но если удалить `~/.local/bin/claude`, система провалится на старую cask-версию.

2. **Разные трекеры версий** – теперь у тебя:
   - Native bun (`~/.local/share/claude/versions/`) обновляется автоматически через `claude update` или внутренний механизм
   - NPM package (`@anthropic-ai/claude-code`) обновляется через `npm update -g`
   - Homebrew cask – через `brew upgrade --cask`
   - Без watcher-а они могут разъехаться, и при следующем `npm install -g @anthropic-ai/claude-code` патчи слетят (потребуется перезапуск `patch-claude-code.sh`)

3. **Скрипт в TMPDIR** – `$TMPDIR` на macOS чистится раз в 3 дня через `/etc/periodic/daily/110.clean-tmps`. Скрипт перенесён в `~/.claude/patch-claude-code.sh` для персистентности.

4. **Риск от --force на npm install** – был разовый, больше применять не нужно: `@anthropic-ai/claude-code` теперь установлен, последующие `npm install -g @anthropic-ai/claude-code` будут проходить нормально.

5. **Патчи привязаны к строкам** – если Anthropic изменит системный промпт в будущей версии, какие-то из 11 патчей начнут показывать `SKIP (not found)`. Скрипт не падает при этом, но выдаёт warning `"WARNING: many patches skipped"` если пропущено >3. Тогда нужно либо ждать обновлённого gist, либо патчить руками.

---
