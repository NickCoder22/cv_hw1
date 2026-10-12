# ДЗ 1 «Фотолаборатория» — отчёт

Отчёт расположен рядом с `photolab.py`, `data/` и `out/`. Команды запускаются из этой папки. 
Для кадров курса:

```bash
IU="$HOME/Documents/iu-intro-cv/lectures/L05-filtering/demo/iu-building.jpg"
L3="$HOME/Documents/iu-intro-cv/lectures/L03-color-histograms/demo"
L4="$HOME/Documents/iu-intro-cv/lectures/L04-geometry/demo"
mkdir -p out/course
```

## 3.1. Цветокоррекция

### Гамма-коррекция

**Задача:** сравнить γ = 0,5 и γ = 2 на одном снимке, измерить яркость до и после.

**Вход:** [data/dark.jpg](data/dark.jpg).

**Команды:**

```bash
python photolab.py gamma data/dark.jpg --gamma 0.5 -o out/dark_g05.jpg --hist out/dark_g05_hist.png | tee out/gamma_g05.json
python photolab.py gamma data/dark.jpg --gamma 2 -o out/dark_g2.jpg --hist out/dark_g2_hist.png | tee out/gamma_g2.json
```

**Выход:** [out/dark_g05.jpg](out/dark_g05.jpg), [out/dark_g2.jpg](out/dark_g2.jpg); гистограммы [out/dark_g05_hist.png](out/dark_g05_hist.png), [out/dark_g2_hist.png](out/dark_g2_hist.png); числа `out/gamma_g05.json`, `out/gamma_g2.json`.

| Вариант | Среднее | Медиана | p1 | p99 | Чёрные, % | Белые, % |
|---|---:|---:|---:|---:|---:|---:|
| Исходник | 76,6 | 74 | 3 | 171 | 0,11 | 0,00 |
| γ = 0,5 | 132,9 | 137 | 23 | 208 | 0,00 | 0,00 |
| γ = 2 | 29,9 | 21 | 0 | 114 | 5,31 | 0,00 |

Показатели рассчитаны по GRAY. 

### Баланс белого

**Задача:** сравнить grey-world и white-patch, измерить усиления и средние каналов.

**Вход:** [data/bright.jpg](data/bright.jpg).

**Команды:**

```bash
python photolab.py wb data/bright.jpg --method grey-world -o out/bright_gw.jpg | tee out/wb_gw.json
python photolab.py wb data/bright.jpg --method white-patch -o out/bright_wp.jpg | tee out/wb_wp.json
```

**Выход:** [out/bright_gw.jpg](out/bright_gw.jpg), [out/bright_wp.jpg](out/bright_wp.jpg); числа `out/wb_gw.json`, `out/wb_wp.json`.

| Метод | Усиление B | Усиление G | Усиление R | Средние до: B; G; R | Средние после: B; G; R |
|---|---:|---:|---:|---|---|
| grey-world | 1,051 | 1,042 | 0,919 | 115,0; 115,9; 131,5 | 120,8; 120,7; 120,8 |
| white-patch | 1,041 | 1,024 | 1,012 | 115,0; 115,9; 131,5 | 119,6; 118,7; 133,0 |



### CLAHE и equalizeHist

**Задача:** сравнить эквализацию канала L в Lab по σ в тенях и среднему в светах.

**Вход:** [data/dark.jpg](data/dark.jpg).

**Команда:**

```bash
python photolab.py clahe data/dark.jpg --clip 2 --tiles 8 -o out/dark_clahe.jpg --compare out/dark_cmp.jpg --hist out/dark_clahe_hist.png | tee out/clahe.json
```

**Выход:** [out/dark_clahe.jpg](out/dark_clahe.jpg); сравнение [out/dark_cmp.jpg](out/dark_cmp.jpg); гистограммы [out/dark_clahe_hist.png](out/dark_clahe_hist.png); числа `out/clahe.json`.

| Вариант | σ в тенях | Среднее в светах |
|---|---:|---:|
| Исходник | 14,3 | 144,5 |
| equalizeHist | 15,0 | 230,0 |
| CLAHE | 18,3 | 159,1 |

Области теней и светов определены по 20-му и 80-му процентилям исходного L; сравниваются одинаковые участки. После CLAHE визуально стал заметнее шум. Ответ с интерпретацией — **5.2, вопрос 3**.

С  equalizeHist меньше шума на светлых участках. С CLAHE есть заметный шум, но надписи на обложке видны лучше. 

## 3.2. Хромакей

### Собственная фотография

**Задача:** выделить предмет по образцу цвета, очистить маску и поставить крупнейшую компоненту на новый фон.

**Вход:** [data/object.jpg](data/object.jpg), [data/bg.jpg](data/bg.jpg).

**Команда:**

```bash
python photolab.py chromakey data/object.jpg --bg data/bg.jpg --sample 346,858,283,194 -o out/object_on_bg.jpg --mask out/object_mask.png | tee out/chromakey.json
```

**Выход:** композит [out/object_on_bg.jpg](out/object_on_bg.jpg), маска [out/object_mask.png](out/object_mask.png); числа `out/chromakey.json`.

| Образец x, y, w, h | Нижняя HSV | Верхняя HSV | Доля маски, % | Компонент до морфологии | После морфологии | После выбора крупнейшей | Дыр |
|---|---|---|---:|---:|---:|---:|---:|
| 346, 858, 283, 194 | 0, 66, 40 | 179, 188, 255 | 11,73 | 137 | 16 | 1 | 4 |

H охватывает все оттенки; выделение ограничено S и V. Ответ о пространстве — **5.2, вопрос 1**. Неудачный первый опыт разобран в **5.3**.

### Recall и precision на ball-lamp.jpg

**Задача:** сравнить маску с эталонным кругом с центром (190, 560) и радиусом 58 px.

**Вход:** `$L3/ball-lamp.jpg`, `$L4/road-cam.jpg`; для метрик — маска и аналитический круг.

**Команды:**

```bash
python photolab.py chromakey "$L3/ball-lamp.jpg" --bg "$L4/road-cam.jpg" --lo 140,121,40 --hi 168,230,255 -o out/course/ck.jpg --mask out/course/ck_mask.png | tee out/course/chromakey.json
python check_course_metrics.py mask --mask out/course/ck_mask.png | tee out/course/ball_metrics.json
```

**Выход:** [out/course/ck.jpg](out/course/ck.jpg), [out/course/ck_mask.png](out/course/ck_mask.png); числа `out/course/chromakey.json`, `out/course/ball_metrics.json`.

| TP | FP | FN | Recall, % | Precision, % | Эталон recall / precision, % |
|---:|---:|---:|---:|---:|---|
| 9987 | 9 | 570 | 94,6007 | 99,91 | 94,6 / 99,9 |

Recall = `100·9987/(9987+570)`; precision = `100·9987/(9987+9)`. После округления метрики совпали с эталоном. Ошибочно выделено 9 пикселей фона, пропущено 570 пикселей объекта.

## 3.3. Геометрия

### Поворот без обрезания

**Задача:** повернуть весь кадр на 30° с увеличением холста.

**Вход:** [data/poster.jpg](data/poster.jpg).

**Команда:**

```bash
python photolab.py rotate data/poster.jpg --deg 30 -o out/poster_rot30.jpg
```

**Выход:** [out/poster_rot30.jpg](out/poster_rot30.jpg); числа выводятся в консоль.

| Угол | Размер до, W × H | Размер после, W × H | Пустой холст, % |
|---|---|---|---:|
| 30° | 1280 × 960 | 1589 × 1472 | 47,5 |

```text
W' = 1280·cos(30°) + 960·sin(30°) = 1588,513 → ceil = 1589
H' = 1280·sin(30°) + 960·cos(30°) = 1471,384 → ceil = 1472
Пустой холст = 100·(1 − 1280·960/(1589·1472)) = 47,465 % → 47,5 %
```

Расчёт совпал с выводом. Доля пустого холста оценивается геометрически.

Углы страницы книги сохранились

### Масштабирование текста

**Задача:** сравнить три способа уменьшения ×0,25 с Pillow Lanczos и отметить потерю штрихов текста.

**Вход:** [data/text.jpg](data/text.jpg).

**Команды:**

```bash
python photolab.py resize data/text.jpg --scale 0.25 --method area --report -o out/text_area.jpg | tee out/resize.json
python photolab.py resize data/text.jpg --scale 0.25 --method blur -o out/text_blur.jpg
python photolab.py resize data/text.jpg --scale 0.25 --method naive -o out/text_naive.jpg
```

**Выход:** [out/text_area.jpg](out/text_area.jpg), [out/text_blur.jpg](out/text_blur.jpg), [out/text_naive.jpg](out/text_naive.jpg); числа `out/resize.json`.

| Метод | Размер результата | PSNR к Pillow Lanczos, дБ |
|---|---|---:|
| naive | 240 × 320 | 32,4 |
| blur | 240 × 320 | 41,9 |
| area | 240 × 320 | 41,8 |

Для blur использовано σ = 1,6. Blur и area ближе к Lanczos, чем naive; разница 0,1 дБ между ними не доказывает разницу читаемости. PSNR рассчитан до JPEG-сжатия.

### Выпрямление собственного объекта

**Задача:** получить фронтальный вид по четырём углам с реальными пропорциями объекта.

**Вход:** [data/poster.jpg](data/poster.jpg).

**Выполненная команда:**

```bash
python photolab.py rectify data/poster.jpg --clicks --aspect 0.73 -o out/poster_front.jpg | tee out/rectify.json
```

**Воспроизведение без кликов:**

```bash
python photolab.py rectify data/poster.jpg --corners 453.33334,141.86667,881.06665,203.73334,1012.26666,706.13336,294.39999,679.46667 --aspect 0.73 -o out/poster_front.jpg | tee out/rectify.json
```

**Выход:** [out/poster_front.jpg](out/poster_front.jpg); числа `out/rectify.json`.

| Верхняя сторона, px | Правая, px | Нижняя, px | Левая, px | Заданный W/H | Размер результата |
|---:|---:|---:|---:|---:|---|
| 432,2 | 519,2 | 718,4 | 560,6 | 0,73 | 718 × 984 |

Ширина = `round(max(432,2; 718,4)) = 718`; высота = `round(718/0,73) = 984`.


### Совпадение с poster-gt.png

**Задача:** выпрямить кадр курса до 640 × 905 и сравнить с эталоном после бинаризации.

**Вход:** `$L4/poster-angle.jpg`, `$L4/poster-gt.png`.

**Команды:**

```bash
python photolab.py rectify "$L4/poster-angle.jpg" --corners 560,330,1250,220,1290,1010,600,840 --size 640x905 -o out/course/front640.png
python check_course_metrics.py poster --front out/course/front640.png --gt "$L4/poster-gt.png" --threshold 127 --diff out/course/poster_diff.png | tee out/course/poster_metrics.json
```

**Выход:** [out/course/front640.png](out/course/front640.png), [out/course/poster_diff.png](out/course/poster_diff.png); числа `out/course/poster_metrics.json`.

| Размер | Порог бинаризации | Пикселей всего | Несовпавших | Совпадение, % | Эталон, % |
|---|---:|---:|---:|---:|---:|
| 640 × 905 | 127 | 579 200 | 5239 | 99,0955 | 99,1 |

Оба изображения переведены в GRAY: белый при яркости >127, чёрный иначе. Совпадение = `100·(1 − 5239/579200)`; после округления получено 99,1 %, как в README. Порог указан для воспроизводимости; точный эталонный порог в README не задан.

## 3.4. Контактный лист

**Задача:** собрать собственные исходники и результаты в ячейках 320 × 240 с сохранением пропорций и подписями «имя WxH».

**Вход:** 18 файлов, перечисленных в команде.

**Команда:**

```bash
python photolab.py sheet \
  data/dark.jpg data/bright.jpg data/object.jpg data/bg.jpg data/poster.jpg data/text.jpg \
  out/dark_g05.jpg out/dark_g2.jpg out/bright_gw.jpg out/bright_wp.jpg \
  out/dark_clahe.jpg out/dark_cmp.jpg out/object_on_bg.jpg out/poster_rot30.jpg \
  out/text_area.jpg out/text_blur.jpg out/text_naive.jpg out/poster_front.jpg \
  --cols 4 -o out/sheet.jpg | tee out/sheet.json
```

**Выход:** [out/sheet.jpg](out/sheet.jpg); числа `out/sheet.json`.

| N | Сетка: строки × столбцы | Размер листа |
|---|---|---|
| [ЗАПОЛНИТЬ из JSON] | [ЗАПОЛНИТЬ] | [ЗАПОЛНИТЬ из JSON] |

Для указанного списка расчёт даёт N = 18, сетку 5 × 4 и размер 1320 × 1378; это расчёт, а не присланный результат запуска. Если использован другой список, изменить команду и таблицу.

**Что проверить:** открыть `out/sheet.jpg`; подписи должны читаться, пропорции сохраняться. В таблицу внести фактический вывод, а сам лист включить в `out/`.

## 5. Обязательные ответы и неудачный результат

### 5.1. Таблицы чисел

Требуемые таблицы размещены в **3.1–3.4**. Значения взяты из консольного вывода; для собственного контактного листа оставлено поле, поскольку его вывод не прислан.

### 5.2. Вопрос 1 — какое пространство выбрано для хромакея и почему; что было бы в RGB?

Использовано HSV: оно разделяет оттенок, насыщенность и яркость, позволяя ограничивать цвет при изменении освещения. В RGB освещение меняет значения сразу трёх каналов, что усложняет выбор диапазона. В моём финальном запуске H = 0–179 охватывал все оттенки, поэтому маска определялась S = 66–188 и V ≥ 40 и занимала 11,73 % кадра. Следовательно, преимущество ограничения по оттенку в этом опыте фактически не использовалось.

### 5.2. Вопрос 2 — как меняется гистограмма при γ < 1 и γ > 1; куда деваются обрезанные пиксели?

При γ = 0,5 распределение смещается к большим значениям: среднее выросло с 76,6 до 132,9, медиана — с 74 до 137. При γ = 2 среднее снизилось до 29,9, медиана — до 21, а доля чёрных выросла с 0,11 % до 5,31 %. Пиксели не удаляются: крайние значения остаются в 0 или 255, а слабые значения после затемнения и округления могут стать нулевыми. Положительная гамма сама сохраняет диапазон 0–255; показатели шаблона считают доли крайних значений, а не новые выходы за диапазон. Полностью чёрный пиксель остаётся чёрным, утраченные детали не восстанавливаются.

### 5.2. Вопрос 3 — почему CLAHE лучше или хуже equalizeHist на моём фото?

CLAHE повысил σ в тенях с 14,3 до 18,3, equalizeHist — до 15,0. Среднее в светах при CLAHE выросло с 144,5 до 159,1, а при equalizeHist — до 230,0: CLAHE изменил света умереннее. Однако после CLAHE в тенях стал заметнее шум, поэтому рост σ нельзя считать исключительно улучшением деталей. На этом фото CLAHE умереннее осветляет света, при этом усиливает шум.

### 5.3. Где сломалось

**Неудачный опыт:** первый хромакей на собственной фотографии.

**Вход:** `data/object.jpg`, `data/bg.jpg`.

**Команда первого запуска:**

```bash
python photolab.py chromakey data/object.jpg --bg data/bg.jpg --sample 305,578,362,545 -o out/object_on_bg.jpg --mask out/object_mask.png | tee out/chromakey.json
```

**Выход первого запуска:** `out/object_on_bg.jpg`, `out/object_mask.png`, `out/chromakey.json`.

Из основного объекта вырван кусок. Причина - наличие на нём другого цвета. 

### 5.4. Команды воспроизведения

Команды и выходные пути основных экспериментов приведены в соответствующих разделах. Для воспроизведения первого неудачного опыта и финального хромакея по одним путям сначала выполнить команду **5.3**, затем **3.2**.

Команды остальных присланных запусков на кадрах курса, чтобы воспроизвести их файлы в `out/course/`:

```bash
python photolab.py gamma "$IU" --gamma 0.5 -o out/course/g05.jpg --hist out/course/g05_hist.png | tee out/course/gamma_g05.json
python photolab.py gamma "$IU" --gamma 2 -o out/course/g20.jpg | tee out/course/gamma_g20.json
python photolab.py wb "$L3/ball-lamp.jpg" --method grey-world -o out/course/wb_gw.jpg | tee out/course/wb_gw.json
python photolab.py wb "$L3/ball-lamp.jpg" --method white-patch -o out/course/wb_wp.jpg | tee out/course/wb_wp.json
python photolab.py rotate "$IU" --deg 30 -o out/course/rot30.jpg | tee out/course/rotate.json
python photolab.py resize "$IU" --scale 0.25 --report -o out/course/small.jpg | tee out/course/resize_small.json
python photolab.py resize "$IU" --scale 2 -o out/course/big.jpg | tee out/course/resize_big.json
python photolab.py rectify "$L4/poster-angle.jpg" --corners 1290,1010,560,330,600,840,1250,220 --aspect 0.707 -o out/course/front.jpg | tee out/course/rectify_aspect.json
python photolab.py sheet "$IU" "$L3/ball-day.jpg" "$L4/poster-angle.jpg" "$L4/road-cam.jpg" "$L4/text-page.png" --cols 3 -o out/course/sheet.jpg | tee out/course/sheet.json
```

