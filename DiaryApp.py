import sys
import os
import cv2
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QTextEdit,
    QMainWindow,
    QDesktopWidget,
    QCalendarWidget,
    QAction,
    qApp,
    QStatusBar,
)
from PyQt5.QtGui import (
    QPixmap,
    QImage,
    QTextCharFormat,
    QIcon,
    QFontDatabase,
    QFont,
    QIcon,
)
from PyQt5.QtCore import QTimer, QUrl, Qt, QDate
from PyQt5.QtMultimedia import QAudioRecorder, QAudioEncoderSettings


class DiaryApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # =========== Commons ===========
        self.DATE_FORMAT = "yyyyMMdd"
        today = QDate.currentDate()
        self.selected_date = today.toString(self.DATE_FORMAT)  # 기본값은 오늘, 캘린더 클릭시 바뀜
        self.is_recording = False

        # 경로 (실행파일로 만들고 다시 봐야할 것 같음, 실행위치 안가져와짐)
        # BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        BASE_DIR = os.getcwd()
        STATIC_DIRS = f"{BASE_DIR}\\static\\"
        self.DATA_DIRS = f"{BASE_DIR}\\data\\"

        # =========== Widgets ===========
        # 이미지
        self.image_label_img = QLabel()
        default_img_file = f"{STATIC_DIRS}default_image.png"
        pixmap = QPixmap(default_img_file)
        pixmap = pixmap.scaledToWidth(400)
        self.image_label_img.setPixmap(pixmap)
        # 미리보기
        self.image_label_video = QLabel()
        self.video_capture = cv2.VideoCapture(0)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)  # 30ms마다 프레임 업데이트
        # 버튼들
        self.camera_button = QPushButton("사진촬영")
        self.camera_button.clicked.connect(self.capture_image)
        self.mic_button = QPushButton("음성 녹음 ●")
        self.mic_button.clicked.connect(self.toggle_recording)
        self.play_button = QPushButton("음성 재생 ▶")
        # - 파일유무에 따라 활성화처리
        self.play_button.setEnabled(False)
        self.trans_button = QPushButton("오디오 → 텍스트 변환")
        self.list_button = QPushButton("목록")
        self.save_button = QPushButton("일기 저장_  오늘도 고생했어요 :)")
        # 캘린더
        self.calendar_widget = QCalendarWidget(self)
        self.calendar_widget.setVerticalHeaderFormat(0)  # vertical header 숨기기
        self.calendar_widget.clicked.connect(self.click_calendar)
        # - 일기쓴 날 표시
        fm = QTextCharFormat()
        fm.setForeground(Qt.blue)
        fm.setBackground(Qt.yellow)
        holidays = ["20231118", "20231126", "20231110", "20231105", "20231102"]
        for dday in holidays:
            dday2 = QDate.fromString(dday, "yyyyMMdd")
            self.calendar_widget.setDateTextFormat(dday2, fm)
        # 상태 메세지 표시
        self.status_label = QLabel()
        # 선택된 날짜 텍스트 표시
        self.date_label = QLabel()
        self.date_label.setAlignment(Qt.AlignHCenter)
        self.click_calendar()
        # 텍스트에디터
        self.text_edit = QTextEdit()

        # ========== left vbox =========
        # 사진-미리보기-촬영버튼-녹음버튼-재생버튼-변환버튼-상태메세지표시
        left_vbox = QVBoxLayout()
        left_vbox.addWidget(self.image_label_img)
        left_vbox.addWidget(self.image_label_video)
        left_vbox.addWidget(self.camera_button)
        button_vbox = QHBoxLayout()
        button_vbox.addWidget(self.mic_button)
        button_vbox.addWidget(self.play_button)
        left_vbox.addLayout(button_vbox)
        left_vbox.addWidget(self.trans_button)
        left_vbox.addWidget(self.status_label)

        # ========== right vbox ==========
        # 일기목록캘린더-날짜텍스트표시-텍스트인풋-저장버튼
        right_vbox = QVBoxLayout()
        right_vbox.addWidget(self.calendar_widget)
        right_vbox.addWidget(self.date_label)
        right_vbox.addWidget(self.text_edit)
        right_vbox.addWidget(self.save_button)

        # ========== outer hbox ==========
        hbox = QHBoxLayout()
        hbox.addLayout(left_vbox)
        hbox.addLayout(right_vbox)

        widget = QWidget()
        widget.setLayout(hbox)
        self.setCentralWidget(widget)

        # ========== 스타일시트 적용 ==========
        button_style = (
            "color: white; background: #C3ACD0; padding:10px; border-radius:4px;"
        )
        button_style_point = (
            "color: white; background: #7743DB; padding:10px; border-radius:4px;"
        )
        self.camera_button.setStyleSheet(button_style)
        self.mic_button.setStyleSheet(button_style)
        self.play_button.setStyleSheet(button_style)
        self.trans_button.setStyleSheet(button_style)
        self.list_button.setStyleSheet(button_style)
        self.save_button.setStyleSheet(button_style_point)
        self.text_edit.setStyleSheet(
            "color: black; background: rgb(240,240,240); padding:10px; border-radius:4px; border: 1px solid #C3ACD0"
        )
        self.date_label.setStyleSheet("padding: 10px;")
        widget.setStyleSheet("background: white; color: #7743DB;")

        # - 폰트 설정
        font_path = f"{STATIC_DIRS}/NotoSansKR-SemiBold.ttf"
        font_id = QFontDatabase.addApplicationFont(font_path)
        font_name = QFontDatabase.applicationFontFamilies(font_id)[0]
        custom_font = QFont(font_name)
        custom_font.setPointSize(11)  # 폰트 크기
        self.camera_button.setFont(custom_font)
        self.mic_button.setFont(custom_font)
        self.play_button.setFont(custom_font)
        self.trans_button.setFont(custom_font)
        self.list_button.setFont(custom_font)
        self.save_button.setFont(custom_font)
        self.status_label.setFont(custom_font)
        self.text_edit.setFont(custom_font)
        self.calendar_widget.setFont(custom_font)
        self.date_label.setFont(custom_font)

        # ========== 창이름 및 사이즈 설정 ==========
        self.setWindowTitle("Face Diary")
        self.setWindowIcon(QIcon(f"{STATIC_DIRS}icon.png"))
        self.setGeometry(800, 900, 800, 900)
        self.center()
        self.show()

    # 화면의 가운데로 띄우기
    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    # ========== 기능1. 카메라 ==========
    # 미리보기
    def update_frame(self):
        try:
            ret, frame = self.video_capture.read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = frame.shape
                bytes_per_line = ch * w
                q_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(q_image)
                pixmap = pixmap.scaledToWidth(400)
                self.image_label_video.setPixmap(pixmap)
        except Exception as e:
            self.status_label.setText(str(e))

    # 캡쳐
    def capture_image(self):
        ret, frame = self.video_capture.read()
        if ret:
            file_name = f"img_{self.selected_date}.jpg"
            file_path = f"{self.DATA_DIRS}\\img\\{file_name}"
            cv2.imwrite(file_path, frame)
            self.status_label.setText("이미지가 캡쳐되었습니다. " + file_name)
            # 이미지 띄우기
            pixmap = QPixmap(file_path)
            pixmap = pixmap.scaledToWidth(400)
            self.image_label_img.setPixmap(pixmap)

    # ========== 기능2. 오디오 ==========
    def toggle_recording(self):
        file_name = f"audio_{self.selected_date}.wav"
        file_path = f"{self.DATA_DIRS}\\audio\\{file_name}"
        if not self.is_recording:
            self.audio_recorder = QAudioRecorder()
            audio_settings = QAudioEncoderSettings()
            audio_settings.setCodec("audio/pcm")
            self.audio_recorder.setAudioSettings(audio_settings)
            self.audio_recorder.setOutputLocation(QUrl.fromLocalFile(file_path))
            self.audio_recorder.record()
            self.is_recording = True
            self.status_label.setText("녹음 중 입니다...")
            self.mic_button.setText("녹음 중지 ■")
        else:
            self.audio_recorder.stop()
            self.is_recording = False
            self.status_label.setText("오디오가 저장되었습니다. " + file_name)
            self.mic_button.setText("음성 녹음 ●")
            self.play_button.setEnabled(True)

    # ========== 기능3. 캘린더 선택(일기조회&수정폼/작성폼) ==========
    def click_calendar(self):
        
        self.selected_date = self.calendar_widget.selectedDate().toString(
            self.DATE_FORMAT
        )
        self.date_label.setText(
            self.calendar_widget.selectedDate().toString("yyyy년 MM월 dd일의 일기")
        )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = DiaryApp()

    sys.exit(app.exec_())
