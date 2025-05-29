#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
نافذة «تهيئة الخشوع» التفاعلية
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
• تتكوّن من ثـماني مراحل: من ختم المهمّة وحتى المكافأة بعد الصلاة.
• لكل مرحلة عنوان واضح + شرح عملي مختصر.
• ينتقل المستخدم للخطوة التالية بالزر «تم».
• عند الوصول إلى النهاية يظهر تنبيه “انتهيت؛ تقبّل الله طاعتك”.
"""

from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QGraphicsDropShadowEffect,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor, QIcon
from PyQt5.QtMultimedia import QSound
import sys, os

# ------------------------------------------------------------------
# ❶ محتوى الخطوات: (عنوان، شرح)
# ------------------------------------------------------------------
STEPS = [
    (
        "خَتمُ المهمّة",
        "احفظ الملف وأغلق التبويبات المفتوحة، ثم اكتب سطرًا: "
        "«أول شيء سأفعله بعد الصلاة هو…» حتى لا ينشغل عقلك بالعمل أثناء الصلاة.",
    ),
    (
        "طقس الإغلاق",
        "قل بصوت مسموع: «انتهيت من العمل حتى بعد الصلاة»، ثم أوقف إشعارات "
        "البورصة والبريد. هذا يُغلق الحلقة الذهنية ويُخفِّض التوتر.",
    ),
    (
        "ميكرو-استراحة جسدية",
        "تمدّد كتفيك 30 ثانية، ثم امش حول الغرفة 30 ثانية؛ الحركة القصيرة "
        "تنعش الدورة الدموية وتطرد الإرهاق الذهني.",
    ),
    (
        "تنفّس مربّع 4-4-4-4",
        "شهيق 4 عدّات → حبس 4 → زفير 4 → حبس 4 (كرِّر 4 دورات). "
        "هذا التمرين يفعّل الجهاز الباراسمبثاوي ويصفّي الذهن.",
    ),
    (
        "وضوء واعٍ",
        "توضّأ بماء فاتر وركّز إحساس الماء على الوجه واليدين. "
        "المحفّز الحسي يساعد الدماغ على «إعادة الضبط».",
    ),
    (
        "نيّة صريحة",
        "قف قبل التكبير وقل: «اللهم إن هذا وقتك، أترك تجارتي إليك»؛ "
        "تثبيت النيّة يطمئن العقل المنطقي ويُحضِّر القلب.",
    ),
    (
        "مفاتيح الخشوع",
        "ركّز إحساس القدمين على السجادة في القيام، امتداد الظهر في الركوع، "
        "ودفء الجبهة في السجود؛ تركيز حسي واحد يحرّر العقل من الشرود.",
    ),
    (
        "مكافأة فورية",
        "بعد التسليم: اكتب نعمةً واحدة أو اشرب رشفة ماء بارد. "
        "اربط الصلاة بمكافأة إيجابية لتثبيت العادة.",
    ),
]

# ------------------------------------------------------------------
# ❷ مسارات الأيقونة والصوت (اختيارية)
# ------------------------------------------------------------------
ICON_PATH  = "assets/mosque.png"          # عدّل إذا لزم
SOUND_PATH = "assets/complete_sound.wav"  # عدّل إذا لزم
if not os.path.exists(SOUND_PATH):
    SOUND_PATH = ""                       # تجاهل الصوت إن لم يوجد

# ------------------------------------------------------------------
# ❸ نافذة الخطوات
# ------------------------------------------------------------------
class StepWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("تهيئة الخشوع")
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setFixedSize(650, 260)
        self.setWindowFlags(
            self.windowFlags()
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.FramelessWindowHint
        )
        # خلفية متدرّجة ناعمة
        self.setStyleSheet(
            """
            QWidget {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #f8f9ff, stop: 1 #e7efff
                );
                border-radius: 12px;
            }
        """
        )

        # ظل دائري خفيف
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(60, 60, 110, 85))
        self.setGraphicsEffect(shadow)

        # تخطيط عمودي
        self.layout = QVBoxLayout(self)
        self.setContentsMargins(32, 24, 32, 22)

        # أيقونة
        if os.path.exists(ICON_PATH):
            icon_lbl = QLabel()
            icon_lbl.setPixmap(QIcon(ICON_PATH).pixmap(48, 48))
            icon_lbl.setAlignment(Qt.AlignCenter)
            self.layout.addWidget(icon_lbl, alignment=Qt.AlignCenter)

        # عنوان الخطوة
        self.title_lbl = QLabel()
        self.title_lbl.setFont(QFont("Cairo", 17, QFont.Bold))
        self.title_lbl.setStyleSheet("color:#243b66;")
        self.title_lbl.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self.layout.addWidget(self.title_lbl)

        # شرح الخطوة
        self.desc_lbl = QLabel()
        self.desc_lbl.setFont(QFont("Cairo", 14))
        self.desc_lbl.setStyleSheet("color:#37474f;")
        self.desc_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.desc_lbl.setWordWrap(True)
        self.layout.addWidget(self.desc_lbl)

        # زر “تم”
        self.btn = QPushButton("تم")
        self.btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn.setFixedHeight(40)
        self.btn.setFont(QFont("Cairo", 14, QFont.Bold))
        self.btn.setStyleSheet(
            """
            QPushButton {
                color: #284c72;
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #f0e9ff, stop:1 #c8e6ff
                );
                border: none;
                border-radius: 14px;
                padding: 0 38px;
            }
            QPushButton:pressed { background: #b9e3ff; }
        """
        )
        self.layout.addWidget(self.btn, alignment=Qt.AlignmentFlag.AlignCenter)

        # مولّد الخطوات
        self.steps = iter(STEPS + [("انتهيت؛ تقبّل الله طاعتك", "")])
        self.btn.clicked.connect(self.next_step)
        self.next_step()

    # تشغيل صوت عند الانتقال
    def play_sound(self):
        if SOUND_PATH:
            try:
                QSound.play(SOUND_PATH)
            except Exception:
                pass

    def next_step(self):
        try:
            title, desc = next(self.steps)
            self.play_sound()

            # عند النهاية
            if not desc:  # السطر الأخير بلا وصف
                self.title_lbl.setText(f"<div dir='rtl' align='center'>{title}</div>")
                self.desc_lbl = QLabel()
                self.btn.setText("إغلاق")
                return

            # نصوص عادية
            self.title_lbl.setText(f"<div dir='rtl' align='center'>{title}</div>")
            self.desc_lbl.setText(f"<div dir='rtl' align='right'>{desc}</div>")
            self.btn.setText("تم")

        except StopIteration:
            self.close()

# ------------------------------------------------------------------
# ❹ نقطة تشغيل مستقلة
# ------------------------------------------------------------------
def run():
    app = QApplication(sys.argv)
    win = StepWindow()
    win.show()
    app.exec_()

# تشغيل مستقل عند تشغيل الملف مباشرة
if __name__ == "__main__":
    run()
