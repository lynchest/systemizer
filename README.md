# 🚀 Systemizer

**Systemizer** is a high-performance, modern, and aesthetically pleasing system monitoring application built with Python and PySide6. It provides real-time insights into your hardware's performance with a focus on efficiency and a smooth user experience.

---

## ✨ Key Features

- **⚡ Real-time Monitoring**: Monitor CPU, RAM, GPU, Disk, and Network usage with high precision.
- **🧵 Multithreaded Architecture**: All data collection happens in background threads, ensuring the UI remains responsive and fluid (60 FPS) at all times.
- **🎮 GPU Optimization**: Smart detection of NVIDIA GPUs with "Lazy Loading" to minimize overhead when a GPU is not present.
- **🔍 Dirty Checking**: Intelligent UI updates—only repaints when data actually changes, drastically reducing CPU/GPU usage.
- **📊 Adaptive Update Rates**:
    - **Fast (1s)**: CPU, RAM, Network (high volatility)
    - **Medium (5s)**: Process Count
    - **Slow (30s)**: Disk Usage, Uptime
- **🎨 Modern UI**: Sleek, glassmorphism-inspired design with smooth animations.

---

## 🛠️ Technology Stack

- **Language**: Python 3.10+
- **UI Framework**: PySide6 (Qt for Python)
- **Metrics**: 
  - `psutil` (System-wide stats)
  - `pynvml` (NVIDIA GPU stats)
- **Packaging**: PyInstaller

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10 or higher
- NVIDIA Drivers (for GPU monitoring)

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/systemizer.git
   cd systemizer
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**:
   ```bash
   python main.py
   ```

---

## ⚙️ Technical Architecture

Systemizer uses a **Thread-Based Architecture** to separate data collection from UI rendering:

1. **DataCollectorThread**: Operates in the background, making system calls without blocking the main event loop.
2. **Signal-Slot Communication**: Uses Qt's thread-safe signal-slot mechanism to pass data to the UI.
3. **Dirty Checking Logic**: Before any UI element is updated, it checks if the new value differs from the current one, preventing unnecessary draw calls.

---

## 🇹🇷 Türkçe Açıklama

**Systemizer**, Python ve PySide6 kullanılarak geliştirilmiş, yüksek performanslı ve modern bir sistem izleme aracıdır. Donanım performansınızı gerçek zamanlı olarak, kullanıcı arayüzünü dondurmadan (60 FPS) izlemenizi sağlar.

**Özellikler:**
- **Arka Plan İşleme**: Tüm veri toplama işlemleri ayrı bir kanalda (thread) yapılır.
- **Akıllı GPU İzleme**: NVIDIA GPU'ları otomatik algılar ve yoksa enerji tasarrufu moduna geçer.
- **Düşük Kaynak Tüketimi**: "Dirty Checking" teknolojisi ile sadece veri değiştiğinde arayüzü günceller.
- **Modern Tasarım**: Şık, modern ve kullanıcı dostu arayüz.

---

## 📄 License
This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

---

## 🤝 Contributing
Contributions are welcome! Feel free to open issues or submit pull requests.

---

*Developed with ❤️ by lynchest*
