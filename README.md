# Video Enhancer

Первый milestone проекта: апскейлинг видео со смартфона с помощью Real-ESRGAN. Скрипт извлекает кадры через FFmpeg, увеличивает их разрешение и собирает MP4, сохраняя исходную аудиодорожку.

## Среда разработки

- Python 3.12;
- установленный FFmpeg (команды `ffmpeg` и `ffprobe` должны быть доступны в `PATH`);
- checkpoint `RealESRGAN_x4plus.pth` в папке `models/`.

Создайте и активируйте виртуальное окружение:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

`requirements.txt` использует CUDA 12.4 сборки PyTorch для NVIDIA GPU; при отсутствии CUDA PyTorch автоматически работает на CPU. Проверка окружения обязательна:

```powershell
python test_environment.py
```

Обработка видео не начнётся, пока эта команда не завершится со статусом `SUCCESS`.

BasicSR 1.4.2 ожидает устаревший путь импорта из torchvision. Проект содержит узкий адаптер `src/compat.py`, который возвращает этот путь к актуальной публичной функции torchvision до импорта Real-ESRGAN.

## Запуск

Скопируйте ролик в `input/`, затем выполните из корня проекта:

```powershell
python src/main.py my_phone_video.mp4 --scale 2
```

Или передайте полный путь:

```powershell
python src/main.py "C:\\Videos\\my_phone_video.mov" --scale 4 --tile 256
```

Результат появится в `output/<имя>_upscaled.mp4`. Опция `--tile 256` уменьшает потребление видеопамяти, но замедляет обработку. Для диагностики добавьте `--verbose`; для сохранения промежуточных кадров — `--keep-temp`.

## Структура

- `src/video.py` — извлечение кадров и сведения о потоке;
- `src/upscale.py` — Real-ESRGAN;
- `src/encoder.py` — кодирование MP4 и возврат аудио;
- `src/effects.py` — простые эффекты, подготовленные для следующего milestone;
- `src/main.py` — минимальный CLI-пайплайн.
