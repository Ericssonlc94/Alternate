> Read this in English: [README.md](README.md)

# 🌀 Severance System

Ferramenta para Windows inspirada na série *Ruptura*. Alterna o computador entre
**Modo Trabalho** e **Modo Pessoal**: encerra os aplicativos do modo anterior,
inicia os do novo, troca o papel de parede e limpa arquivos temporários.

O projeto tem **duas interfaces sobre o mesmo núcleo**: uma GUI em PySide6
(principal) e a CLI original em `rich`.

---

## 📁 Estrutura do projeto

```
Severance-System/
├── assets/                  recursos somente-leitura (vão embarcados no .exe)
│   ├── lang/
│   │   ├── pt.json
│   │   └── en.json
│   └── logo.ico
├── data/                    dados do usuário (ficam AO LADO do .exe)
│   ├── config.json
│   ├── work_apps.json
│   ├── personal_apps.json
│   └── virtual_desktops_backup.json
├── docs/
│   └── manual_python_estudo.md
├── logs/                    reservada (ver "Limitações conhecidas")
├── packaging/
│   └── severance_system.spec
├── src/
│   ├── core.py              motor: processos, wallpaper, registro, limpeza
│   ├── severance_system.py  interface CLI (rich)
│   └── gui/                 interface gráfica (PySide6)
├── run.bat                  abre a CLI
├── run_gui.bat              abre a GUI
└── requirements.txt
```

### Por que `data/` e `assets/` são separados

Não é organização cosmética: as duas pastas têm ciclos de vida diferentes quando
o programa é empacotado com PyInstaller.

- **`assets/`** é somente-leitura e vai *dentro* do executável. Ao rodar, o
  PyInstaller descompacta esse conteúdo numa pasta temporária nova a cada
  execução (`sys._MEIPASS`).
- **`data/`** é gravável e precisa **sobreviver** ao fechamento do programa. Se
  o `config.json` fosse embarcado junto dos assets, cada execução começaria com
  a pasta temporária zerada e as suas configurações seriam perdidas.

Quem resolve isso é a camada de caminhos do `core.py`:

| Função | Devolve | Empacotado (`.exe`) |
|---|---|---|
| `get_project_root()` | raiz do projeto | pasta do executável |
| `get_data_dir()` | `data/` (cria se faltar) | `data/` ao lado do `.exe` |
| `get_logs_dir()` | `logs/` (cria se faltar) | `logs/` ao lado do `.exe` |
| `get_asset_path(*p)` | `assets/...` | `sys._MEIPASS/assets/...` |

`get_project_root()` resolve a raiz a partir de `__file__` — **nunca** do
diretório de trabalho. Por isso o programa acha `data/` e `assets/` corretamente
seja qual for a pasta de onde foi iniciado (atalho, terminal ou agendador).

---

## ⚙️ Instalação

Requisitos: **Windows** e **Python 3.13** (testado em 3.13.7 com PySide6 6.11).
O projeto usa APIs exclusivas do Windows (`winreg`, `ctypes.windll`, `winsound`).

```bash
python -m venv venv
venv\Scripts\pip install -r requirements.txt
```

---

## ▶️ Como executar

| Comando | O que abre |
|---|---|
| `run_gui.bat` | GUI (recomendado) — usa `pythonw.exe`, sem console atrás |
| `run.bat` | CLI em modo texto |

Manualmente:

```bash
cd src
..\venv\Scripts\python.exe -m gui          # GUI
..\venv\Scripts\python.exe severance_system.py   # CLI
```

O diretório de trabalho é `src\` para que `-m gui` encontre o pacote e o
`import core` resolva sem `PYTHONPATH`. Os caminhos de `data/` e `assets/` não
dependem disso.

---

## 🖥️ A interface gráfica

**Abertura** — o boot da ROBCO-LUMON INDUSTRIES, com efeito de fósforo,
scanlines e digitação. Pode ser pulada.

**Tela de bloqueio** — reproduz o minigame de senha do terminal ROBCO Termlink
(*Fallout*): palavras escondidas num despejo de memória, quatro tentativas e a
dica de *likeness*. Ativável em Ajustes › "Iniciar bloqueado".
⚠️ **É uma brincadeira, não segurança.** Não protege nem esconde nada: qualquer
um que abra `data/config.json` ou rode a CLI passa por cima dela.

**Aba Controle** — iniciar Modo Trabalho, iniciar Modo Pessoal, limpar cache e
temporários. Um painel de log mostra cada processo encerrado/iniciado.

**Aba Banco de Dados** — lista os apps de cada modo, com adicionar e excluir.

**Ajustes (⚙)** — nome de usuário, idioma, tema, iniciar bloqueado, efeitos
sonoros, papel de parede e restaurar ao padrão.

**Temas** — `severance` (padrão) e `fallout`.

**Bandeja** — a janela minimiza para a bandeja em vez de fechar.

Nenhuma ação roda na thread da interface: tudo passa por um `Worker`, e os
eventos voltam como *signals* Qt. A janela não congela durante uma troca de modo.

---

## ⌨️ A interface de linha de comando

| Opção | Função |
|---|---|
| **1** | Iniciar Modo Trabalho |
| **2** | Iniciar Modo Pessoal |
| **3** | Adicionar app ao banco de dados |
| **4** | Consultar banco de dados |
| **5** | Excluir app do banco de dados |
| **6** | Adicionar papel de parede |
| **7** | Limpar cache/temporários **+ desktops virtuais órfãos** |
| **8** | Restaurar ao padrão |
| **9** | Sair |
| **\*** | Alternar idioma (pt ⇄ en) |

---

## 🗂️ Configuração e dados

### `data/config.json`

| Campo | Descrição |
|---|---|
| `language` | `pt` ou `en` |
| `user_name` | seu nome (*innie*) |
| `active_mode` / `active_mode_key` | último modo iniciado |
| `work_wallpaper` / `personal_wallpaper` | `{ "path": ..., "style": "1".."6" }` |
| `theme` | `severance` ou `fallout` |
| `start_locked` | abrir na tela de bloqueio |
| `sound_enabled` | efeitos sonoros do terminal |
| `wallpaper_walk_desktops` | percorrer as áreas de trabalho ao aplicar o papel de parede (padrão: `true`) |

### `data/work_apps.json` e `data/personal_apps.json`

```json
[
    {
        "name": "DROPBOX",
        "path": "C:/Program Files (x86)/Dropbox/Client/Dropbox.exe",
        "close_after_launch": true,
        "requires_admin": true
    }
]
```

| Campo | Efeito |
|---|---|
| `name` | rótulo exibido; também casa a janela em `close_after_launch` |
| `path` | caminho do `.exe` ou `.vbs` (`.vbs` roda via `wscript.exe`) |
| `close_after_launch` | fecha a **interface** do app após iniciar (Alt+F4), deixando o processo de fundo vivo |
| `requires_admin` | inicia elevado (`runas`), com prompt do UAC |

Apps presentes nos **dois** modos não são encerrados na troca — só os exclusivos
do modo anterior. Steam e Dropbox têm tratamento especial (`-silent`, encerramento
mais agressivo, silenciamento da saída).

### Estilos de papel de parede

| Código | Estilo |
|---|---|
| `1` | Preencher |
| `2` | Ajustar |
| `3` | Esticar |
| `4` | Lado a lado |
| `5` | Centralizar |
| `6` | Span (múltiplos monitores) |

#### Múltiplas áreas de trabalho virtuais

O papel de parede é aplicado em **todas** as áreas de trabalho virtuais, não só
na ativa. Isso exige um rodeio: `SystemParametersInfoW` repinta apenas a área
ativa, e gravar a chave `Wallpaper` de cada GUID no registro **não basta** — o
Explorer mantém o papel de parede de cada área em memória e só consulta essas
chaves ao iniciar a sessão.

Por isso o sistema faz as duas coisas: grava o registro (para o valor estar certo
no próximo login) e **percorre as áreas** com `Ctrl+Win+Seta`, aplicando de fato
em cada uma e voltando à área de origem no fim. O efeito visível é a tela
alternar por alguns segundos durante a troca de modo.

O percurso só acontece quando há algo a mudar: se o papel de parede alvo (e o
estilo) já estiverem em vigor em todas as áreas, essa etapa é pulada por
completo. Iniciar o mesmo modo duas vezes seguidas não alterna nada.

Para desativar esse percurso — ficando só com a área ativa e o registro —
acrescente ao `data/config.json`:

```json
"wallpaper_walk_desktops": false
```

### Traduções

Cada arquivo em `assets/lang/` vira um idioma automaticamente (o código é o nome
do arquivo). Para adicionar um idioma, copie `pt.json`, traduza os valores e
salve como, por exemplo, `es.json`.

---

## 🧱 Arquitetura

O núcleo não conhece `rich`, Qt nem idioma. Ele reporta o que está fazendo
através do contrato `core.Reporter`, e cada interface implementa o seu:

```
severance_system.py ── RichReporter ─┐
                                     ├─→ core.Reporter ──→ core.py
gui/ ───────────────── QtReporter ───┘                     (processos, registro,
                                                            wallpaper, limpeza)
```

| Módulo em `src/gui/` | Papel |
|---|---|
| `__main__.py` / `app.py` | ponto de entrada (`python -m gui`) |
| `main_window.py` | `QStackedWidget`: boot → bloqueio → abas |
| `boot.py` | abertura ROBCO-LUMON |
| `lockscreen.py` | minigame do terminal Termlink |
| `dialogs.py` | formulários de app, ajustes e papel de parede |
| `effects.py` | overlay CRT: fósforo, scanlines, varredura |
| `theme.py` | paletas Severance/Fallout (QSS via `string.Template`) |
| `sound.py` | tons WAV assíncronos em memória |
| `reporter.py` | `Worker` + ponte núcleo → signals Qt |
| `i18n.py` | tradução em runtime, limpando a marcação do `rich` |

---

## 📦 Gerar o executável

A partir da **raiz** do projeto:

```bash
venv\Scripts\pyinstaller packaging\severance_system.spec
```

O `.spec` embarca `assets/` e mantém `data/` de fora — de propósito, para que a
configuração do usuário fique ao lado do executável e sobreviva às atualizações.

---

## ⚠️ Limitações conhecidas

- **A receita de build gera apenas a CLI.** O `.spec` aponta para
  `src/severance_system.py`; ainda não há build da GUI.
- **`logs/` não é usada por nada.** A pasta e o `core.get_logs_dir()` existem,
  mas o projeto não tem sistema de log — é estrutura pronta, não recurso ativo.
- **A limpeza de desktops virtuais órfãos só existe na CLI** (opção 7). A GUI
  limpa cache e temporários, mas não chama `clean_orphan_virtual_desktops()`.
- **Somente Windows.** `winreg`, `ctypes.windll` e `winsound` não têm equivalente
  nas outras plataformas.
- A limpeza de temporários ignora arquivos em uso pelo sistema — é esperado ver
  vários "permissão negada" no log.
