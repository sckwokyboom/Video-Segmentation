import imageio
from skimage.color import rgb2gray
from skimage.metrics import structural_similarity as ssim
import moviepy


# Функция для вычисления процентной разницы между двумя кадрами
def calculate_frame_difference(frame1, frame2):
    gray_frame1 = rgb2gray(frame1)
    gray_frame2 = rgb2gray(frame2)

    # Предполагаем, что значения пикселей находятся в диапазоне [0, 1]
    score, _ = ssim(gray_frame1, gray_frame2, full=True, data_range=1.0)
    return score


# Функция для фильтрации видео по кадрам
def filter_similar_frames(video_path, similarity_threshold=0.7):
    reader = imageio.get_reader(uri=video_path)
    fps = reader.get_meta_data()['fps']
    writer = imageio.get_writer('output_filtered_04_threshold.mp4', fps=fps)

    prev_frame = None

    for i, frame in enumerate(reader):
        if prev_frame is None:
            prev_frame = frame
            writer.append_data(frame)  # Сохраняем первый кадр
            continue

        # Вычисляем сходство между кадрами
        similarity = calculate_frame_difference(prev_frame, frame)

        # Сохраняем кадр, если он отличается больше, чем на порог (например, 70%)
        if similarity < similarity_threshold:
            writer.append_data(frame)
            prev_frame = frame  # Обновляем предыдущий кадр

    reader.close()
    writer.close()
    print("Видео успешно отфильтровано и сохранено как 'output_filtered.mp4'")


# Запуск фильтрации
video_path = 'C:\\Users\\sckwo\\PycharmProjects\\Video-Segmentation\\video.mp4'
filter_similar_frames(video_path, similarity_threshold=0.4)
