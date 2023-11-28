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
    QFileDialog
)
from PyQt5.QtGui import (
    QPixmap,
    QImage,
    QTextCharFormat,
    QIcon,
    QFontDatabase,
    QFont,
    QIcon,
    QColor,
)
from PyQt5.QtCore import QTimer, QUrl, Qt, QDate
from PyQt5.QtMultimedia import QAudioRecorder, QAudioEncoderSettings
import speech_recognition as sr
import playsound

from PIL import Image
from datetime import datetime
import sqlite3

# pip install playsound==1.2.2


class ManageDiary:
    def __init__(self):
        DB_FILE_PATH = "diary.db"
        self.db_file = DB_FILE_PATH
        self.create_table()

    def create_table(self):
        try:
            conn = sqlite3.connect(self.db_file)
            c = conn.cursor()
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS diary (
                    date INTEGER PRIMARY KEY,
                    content TEXT,
                    img_file_name TEXT,
                    audio_file_name TEXT
                )
            """
            )
            conn.commit()
        except sqlite3.Error as e:
            print(f"Error creating table: {e}")
        finally:
            conn.close()

    def add_entry(self, date, content, img_file_name, audio_file_name):
        result = False
        try:
            conn = sqlite3.connect(self.db_file)
            c = conn.cursor()
            c.execute(
                """
                INSERT INTO diary (date, content, img_file_name, audio_file_name)
                VALUES (?, ?, ?, ?)
            """,
                (date, content, img_file_name, audio_file_name),
            )
            conn.commit()
            result = True
        except sqlite3.Error as e:
            print(f"Error adding entry: {e}")
        finally:
            conn.close()
            return result

    def view_entries(self):
        try:
            conn = sqlite3.connect(self.db_file)
            c = conn.cursor()
            c.execute(
                """
                SELECT * FROM diary
            """
            )
            entries = c.fetchall()
            return entries
        except sqlite3.Error as e:
            print(f"Error viewing entries: {e}")
        finally:
            conn.close()

    def view_entry(self, date):
        try:
            conn = sqlite3.connect(self.db_file)
            c = conn.cursor()
            c.execute(
                """
                SELECT * FROM diary WHERE date = ?
            """,
                [date],
            )
            entry = c.fetchone()
            return entry
        except sqlite3.Error as e:
            print(f"Error viewing entry: {e}")
        finally:
            conn.close()

    def update_entry(self, date, content, img_file_name, audio_file_name):
        result = False
        try:
            conn = sqlite3.connect(self.db_file)
            c = conn.cursor()
            c.execute(
                """
                UPDATE diary
                SET content = ?, img_file_name = ?, audio_file_name = ?
                WHERE date = ?
            """,
                (content, img_file_name, audio_file_name, date),
            )
            conn.commit()
            result = True
        except sqlite3.Error as e:
            print(f"Error updating entry: {e}")
        finally:
            conn.close()
            return result

    def delete_entry(self, entry_id):
        result = False
        try:
            conn = sqlite3.connect(self.db_file)
            c = conn.cursor()
            c.execute(
                """
                DELETE FROM diary
                WHERE date = ?
            """,
                (entry_id,),
            )
            conn.commit()
            result = True
        except sqlite3.Error as e:
            print(f"Error deleting entry: {e}")
        finally:
            conn.close()
            return result


class Diary(QMainWindow):
    def __init__(self):
        super().__init__()

        self.manageDiary = ManageDiary()
        # 테이블 생성
        self.manageDiary.create_table()

        self.initUI()

    def initUI(self):
        # =========== Commons ===========
        self.DATE_FORMAT = "yyyyMMdd"
        today = QDate.currentDate()
        self.selected_date = today.toString(self.DATE_FORMAT)  # 기본값은 오늘, 캘린더 클릭시 바뀜
        self.is_recording = False
        self.is_diary_exist = False
        self.img_file_name = ""
        self.audio_file_name = ""

        # 경로 (실행파일로 만들고 다시 봐야할 것 같음, 실행위치 안가져와짐)
        # BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        BASE_DIR = os.getcwd()
        STATIC_DIRS = f"{BASE_DIR}\\static\\"
        self.DATA_DIRS = f"{BASE_DIR}\\data\\"
        self.DEFAULT_IMG_PATH = f"{STATIC_DIRS}default_image.png"

        # =========== Widgets ===========
        # 이미지
        self.image_label_img = QLabel()
        self.paint_img(self.DEFAULT_IMG_PATH)

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
        self.play_button.clicked.connect(self.play_recoding)
        # - 파일유무에 따라 활성화처리
        self.play_button.setEnabled(False)
        # self.trans_button = QPushButton("오디오 → 텍스트 변환")
        self.list_button = QPushButton("목록")
        self.save_button = QPushButton("저장_  오늘도 고생했어요 :)")
        self.save_button.clicked.connect(self.save_diary)
        self.delete_button = QPushButton("삭제")
        self.delete_button.clicked.connect(self.delete_diary)
        # 캘린더
        self.calendar_widget = QCalendarWidget(self)
        self.calendar_widget.setVerticalHeaderFormat(0)  # vertical header 숨기기
        self.calendar_widget.clicked.connect(self.view_diary)
        # 상태 메세지 표시
        self.status_label = QLabel()
        # 선택된 날짜 텍스트 표시
        self.date_label = QLabel()
        self.date_label.setAlignment(Qt.AlignHCenter)
        # 이미지 파일 텍스트 표시
        self.img_file_label = QLabel()
        self.img_file_label.setAlignment(Qt.AlignHCenter)
        # 오디오 파일 텍스트 표시
        self.audio_file_label = QLabel()
        self.audio_file_label.setAlignment(Qt.AlignHCenter)
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
        # left_vbox.addWidget(self.trans_button)
        left_vbox.addWidget(self.img_file_label)
        left_vbox.addWidget(self.audio_file_label)
        left_vbox.addWidget(self.status_label)

        # ========== right vbox ==========
        # 일기목록캘린더-날짜텍스트표시-텍스트인풋-저장버튼
        right_vbox = QVBoxLayout()
        right_vbox.addWidget(self.calendar_widget)
        right_vbox.addWidget(self.date_label)
        right_vbox.addWidget(self.text_edit)
        diary_buttons_vbox = QHBoxLayout()
        diary_buttons_vbox.addWidget(self.delete_button)
        diary_buttons_vbox.addWidget(self.save_button)
        right_vbox.addLayout(diary_buttons_vbox)

        # ========== outer hbox ==========
        hbox = QHBoxLayout()
        hbox.addLayout(left_vbox)
        hbox.addLayout(right_vbox)

        widget = QWidget()
        widget.setLayout(hbox)
        self.setCentralWidget(widget)

        # ========== 앱 상태표시줄 생성 ==========
        self.statusbar = QStatusBar(self)
        self.setStatusBar(self.statusbar)
        # self.statusBar()
        # .setStatusTip("Exit application")으로 상태표시줄 문구 표시 가능

        # ========== 메뉴바 생성 ==========
        # 설정 - 사진 GIF로 만들기, 비밀번호 설정
        createGifAction = QAction("GIF 생성", self)
        createGifAction.triggered.connect(self.images_to_gif)
        setPasswordAction = QAction("비밀번호 변경", self)
        exitAction = QAction("종료", self)
        exitAction.setShortcut("Ctrl+Q")
        exitAction.setStatusTip("Exit application")
        exitAction.triggered.connect(qApp.quit)
        menubar = self.menuBar()
        menubar.setNativeMenuBar(False)
        settings_menu = menubar.addMenu("&설정")
        settings_menu.addAction(createGifAction)
        settings_menu.addAction(setPasswordAction)
        settings_menu.addAction(exitAction)

        # ========== 스타일시트 적용 ==========
        self.BUTTON_STYLE = (
            "color: white; background: #C3ACD0; padding:10px; border-radius:4px;"
        )
        self.BUTTON_STYLE_POINT = (
            "color: white; background: #7743DB; padding:10px; border-radius:4px;"
        )
        self.camera_button.setStyleSheet(self.BUTTON_STYLE)
        self.mic_button.setStyleSheet(self.BUTTON_STYLE)
        self.play_button.setStyleSheet(self.BUTTON_STYLE)
        # self.trans_button.setStyleSheet(BUTTON_STYLE)
        self.list_button.setStyleSheet(self.BUTTON_STYLE)
        self.delete_button.setStyleSheet(self.BUTTON_STYLE)
        self.save_button.setStyleSheet(self.BUTTON_STYLE_POINT)
        self.text_edit.setStyleSheet(
            "color: black; background: rgb(255, 251, 245); padding:10px; border-radius:4px; border: 1px solid #C3ACD0"
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
        # self.trans_button.setFont(custom_font)
        self.list_button.setFont(custom_font)
        self.delete_button.setFont(custom_font)
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
        self.view_diary()
        entries = self.manageDiary.view_entries()
        for dday in entries:
            self.mark_calendar(str(dday[0]))
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

            self.img_file_name = file_name  # 일기저장할 때 사용
            self.status_label.setText("이미지가 캡쳐되었습니다. " + file_name)
            # 이미지띄우기
            self.paint_img(file_path)

    # ========== 기능2. 오디오 ==========
    # 오디오 녹음/정지
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
            self.mic_button.setStyleSheet(self.BUTTON_STYLE_POINT)
        else:
            self.audio_recorder.stop()
            self.is_recording = False
            self.audio_file_name = file_name
            self.status_label.setText("오디오가 저장되었습니다. " + file_name)
            self.mic_button.setText("음성 녹음 ●")
            self.play_button.setEnabled(True)
            self.mic_button.setStyleSheet(self.BUTTON_STYLE)

            # 오디오->텍스트 변환
            try:
                r = sr.Recognizer()
                with sr.AudioFile(file_path) as source:
                    audio = r.record(source, duration=120)
                    vToText = r.recognize_google(audio_data=audio, language="ko-KR")
                    text = self.text_edit.toPlainText()
                    text += vToText + "\n"
                    self.text_edit.setText(text)
            except sr.UnknownValueError:
                self.status_label.setText("음성을 인식하지 못했습니다. 다시 녹음해주세요.")

    # 오디오 재생
    def play_recoding(self):
        file_path = f"{self.DATA_DIRS}\\audio\\{self.audio_file_name}"
        if os.path.exists(file_path):
            playsound.playsound(file_path)

    # ========== 기능3. 일기관리 ==========
    # 일기조회(=캘린더 날짜 클릭)
    def view_diary(self):
        # 선택된 날짜(전역변수) 값 셋팅 및 표시
        self.selected_date = self.calendar_widget.selectedDate().toString(
            self.DATE_FORMAT
        )
        self.date_label.setText(
            self.calendar_widget.selectedDate().toString("yyyy년 MM월 dd일의 일기")
        )
        # 저장된 데이터 있는지 조회 및 셋팅
        entry = self.manageDiary.view_entry(self.selected_date)
        if entry:
            self.is_diary_exist = True
            self.status_label.setText("해당 날짜의 일기가 있습니다.")
            self.paint_ui(entry[1], entry[2], entry[3])
        else:
            self.is_diary_exist = False
            self.status_label.setText("데이터 없음")
            self.paint_ui("", "", "")

    # 일기저장
    # - 저장할 정보: 날짜, 텍스트, 이미지파일이름, 오디오파일이름
    def save_diary(self):
        if self.is_diary_exist:  # 해당 날짜 일기 조회 시마다 셋팅되는 변수
            # 있으면 업데이트
            result = self.manageDiary.update_entry(
                self.selected_date,
                self.text_edit.toPlainText(),
                self.img_file_name,
                self.audio_file_name,
            )
            if result:
                self.status_label.setText("일기가 수정되었습니다.")
            else:
                self.status_label.setText("일기 수정에 실패했습니다. 다시 시도해주세요.")
        else:
            # 없으면 추가
            result = self.manageDiary.add_entry(
                self.selected_date,
                self.text_edit.toPlainText(),
                self.img_file_name,
                self.audio_file_name,
            )
            if result:
                self.status_label.setText("일기가 저장되었습니다.")
                self.mark_calendar(self.selected_date)
            else:
                self.status_label.setText("일기 저장에 실패했습니다. 다시 시도해주세요.")

    # 일기삭제
    def delete_diary(self):
        result = self.manageDiary.delete_entry(self.selected_date)
        if result:
            self.status_label.setText("일기가 삭제되었습니다.")
            self.paint_ui("", "", "")
        else:
            self.status_label.setText("삭제가 실패했습니다. 다시 시도해주세요.")

    # ========== ui에 데이터바인딩 (디폴트 화면, 일기조회시, 삭제시) ==========
    def paint_ui(self, content, img_file_name, audio_file_name):
        # 이미지
        if img_file_name == "":
            self.paint_img(self.DEFAULT_IMG_PATH)
        else:
            file_name = f"img_{self.selected_date}.jpg"
            file_path = f"{self.DATA_DIRS}\\img\\{file_name}"
            self.paint_img(file_path)
        # 오디오
        if audio_file_name != "":
            self.audio_file_name = audio_file_name

        self.text_edit.setText(content)
        self.img_file_label.setText(img_file_name)
        self.audio_file_label.setText(audio_file_name)

    # 이미지 띄우기
    def paint_img(self, file_path):
        pixmap = QPixmap(file_path)
        pixmap = pixmap.scaledToWidth(400)
        self.image_label_img.setPixmap(pixmap)

    # 일기 쓴 날 캘린더에 표시
    def mark_calendar(self, date):
        fm = QTextCharFormat()
        fm.setForeground(Qt.white)
        # fm.setBackground(QColor(119, 67, 219, 255))
        fm.setBackground(QColor(195, 172, 208, 255))
        dday2 = QDate.fromString(date, self.DATE_FORMAT)
        self.calendar_widget.setDateTextFormat(dday2, fm)

    
    # 이미지를 gif로 변환
    def images_to_gif(self):
         # # 폴더명 설정
        # image_folder_path =  # 사진 폴더
        # gif_output_path =  # gif 저장 폴더
        # images_to_gif(image_folder_path, gif_output_path)
        duration=500
        input_folder = 'img'
        output_path= 'output.gif'
        # 입력 폴더의 모든 이미지 파일에 대해 변환 수행
        image_files = [f for f in os.listdir(input_folder) if f.endswith(('.jpg', '.jpeg', '.png', '.gif'))]
        images = [Image.open(os.path.join(input_folder, f)) for f in image_files]
        
        # GIF로 저장할 때 애니메이션 속도를 조절할 수 있습니다.
        # duration은 각 프레임의 표시 시간을 밀리초로 나타냅니다.
        images[0].save(output_path, save_all=True, append_images=images[1:], duration=duration, loop=0)

        


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = Diary()

    sys.exit(app.exec_())

# DB 조회 시나리오
# 맨처음프로그램 실행시
# - 현재 캘린더 페이지 일기 쓴 날 체크
# - 오늘 날짜 일기 데이터 체크
# 캘린더 페이지 변경시
# - 현재 캘린더 페이지 일기 쓴 날 체크
# 날짜 변경시
# - 변경한 날짜 일기 데이터 체크

# 일기 저장할때 insert, 수정힐때 update, 일기 내용 지울때 delete

# 저장된 이미지파일 오디오파일 체크하고 UI에 표시해야겠다
