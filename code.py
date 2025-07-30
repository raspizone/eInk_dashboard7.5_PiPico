

from machine import Pin, SPI
import framebuf
import utime
import urequests
import network
import sys
import calendar


# Configuración WiFi
SSID = 'ssid'
PASSWORD = 'pass'

# Display resolution
EPD_WIDTH       = 800
EPD_HEIGHT      = 480

RST_PIN         = 12
DC_PIN          = 8
CS_PIN          = 9
BUSY_PIN        = 13

class EPD_7in5_B:
    def __init__(self):
        self.reset_pin = Pin(RST_PIN, Pin.OUT)
        
        self.busy_pin = Pin(BUSY_PIN, Pin.IN, Pin.PULL_UP)
        self.cs_pin = Pin(CS_PIN, Pin.OUT)
        self.width = EPD_WIDTH
        self.height = EPD_HEIGHT
        self.partFlag=1
        
        self.spi = SPI(1)
        self.spi.init(baudrate=4000_000)
        self.dc_pin = Pin(DC_PIN, Pin.OUT)
        

        self.buffer_black = bytearray(self.height * self.width // 8)
        self.buffer_red = bytearray(self.height * self.width // 8)
        self.imageblack = framebuf.FrameBuffer(self.buffer_black, self.width, self.height, framebuf.MONO_HLSB)
        self.imagered = framebuf.FrameBuffer(self.buffer_red, self.width, self.height, framebuf.MONO_HLSB)
        self.init()

    def digital_write(self, pin, value):
        pin.value(value)

    def digital_read(self, pin):
        return pin.value()

    def delay_ms(self, delaytime):
        utime.sleep(delaytime / 1000.0)

    def spi_writebyte(self, data):
        self.spi.write(bytearray(data))

    def module_exit(self):
        self.digital_write(self.reset_pin, 0)

    # Hardware reset
    def reset(self):
        self.digital_write(self.reset_pin, 1)
        self.delay_ms(200) 
        self.digital_write(self.reset_pin, 0)
        self.delay_ms(2)
        self.digital_write(self.reset_pin, 1)
        self.delay_ms(200)   

    def send_command(self, command):
        self.digital_write(self.dc_pin, 0)
        self.digital_write(self.cs_pin, 0)
        self.spi_writebyte([command])
        self.digital_write(self.cs_pin, 1)

    def send_data(self, data):
        self.digital_write(self.dc_pin, 1)
        self.digital_write(self.cs_pin, 0)
        self.spi_writebyte([data])
        self.digital_write(self.cs_pin, 1)
        
    def send_data1(self, buf):
        self.digital_write(self.dc_pin, 1)
        self.digital_write(self.cs_pin, 0)
        self.spi.write(bytearray(buf))
        self.digital_write(self.cs_pin, 1)

    def WaitUntilIdle(self):
        print("e-Paper busy")
        while(self.digital_read(self.busy_pin) == 0):   # Wait until the busy_pin goes LOW
            self.delay_ms(20)
        self.delay_ms(20) 
        print("e-Paper busy release")  

    def TurnOnDisplay(self):
        self.send_command(0x12) # DISPLAY REFRESH
        self.delay_ms(100)      #!!!The delay here is necessary, 200uS at least!!!
        self.WaitUntilIdle()
        
    def init(self):
        # EPD hardware init start     
        self.reset()
        
        self.send_command(0x06)     # btst
        self.send_data(0x17)
        self.send_data(0x17)
        self.send_data(0x28)        # If an exception is displayed, try using 0x38
        self.send_data(0x17)
        
#         self.send_command(0x01)  # POWER SETTING
#         self.send_data(0x07)
#         self.send_data(0x07)     # VGH=20V,VGL=-20V
#         self.send_data(0x3f)     # VDH=15V
#         self.send_data(0x3f)     # VDL=-15V
        
        self.send_command(0x04)  # POWER ON
        self.delay_ms(100)
        self.WaitUntilIdle()

        self.send_command(0X00)   # PANNEL SETTING
        self.send_data(0x0F)      # KW-3f   KWR-2F	BWROTP 0f	BWOTP 1f

        self.send_command(0x61)     # tres
        self.send_data(0x03)     # source 800
        self.send_data(0x20)
        self.send_data(0x01)     # gate 480
        self.send_data(0xE0)

        self.send_command(0X15)
        self.send_data(0x00)

        self.send_command(0X50)     # VCOM AND DATA INTERVAL SETTING
        self.send_data(0x11)
        self.send_data(0x07)

        self.send_command(0X60)     # TCON SETTING
        self.send_data(0x22)

        self.send_command(0x65)     # Resolution setting
        self.send_data(0x00)
        self.send_data(0x00)     # 800*480
        self.send_data(0x00)
        self.send_data(0x00)
        
        return 0;
    
    def init_Fast(self):
        # EPD hardware init start
        self.reset()

        self.send_command(0X00)
        self.send_data(0x0F)

        self.send_command(0x04)
        self.delay_ms(100)
        self.WaitUntilIdle()

        self.send_command(0x06)
        self.send_data(0x27)
        self.send_data(0x27) 
        self.send_data(0x18)		
        self.send_data(0x17)		

        self.send_command(0xE0)
        self.send_data(0x02)
        self.send_command(0xE5)
        self.send_data(0x5A)

        self.send_command(0X50)
        self.send_data(0x11)
        self.send_data(0x07)
        
        return 0
    
    def init_part(self):
        # EPD hardware init start
        self.reset()

        self.send_command(0X00)
        self.send_data(0x1F)

        self.send_command(0x04)
        self.delay_ms(100)
        self.WaitUntilIdle()

        self.send_command(0xE0)
        self.send_data(0x02)
        self.send_command(0xE5)
        self.send_data(0x6E)

        self.send_command(0X50)
        self.send_data(0xA9)
        self.send_data(0x07)

        # EPD hardware init end
        return 0
    
    
    def Clear(self):
        high = self.height
        if( self.width % 8 == 0) :
            wide =  self.width // 8
        else :
            wide =  self.width // 8 + 1
        
        self.send_command(0x10)
        for i in range(0, wide):
            self.send_data1([0xff] * high)
                
        self.send_command(0x13) 
        for i in range(0, wide):
            self.send_data1([0x00] * high)
                
        self.TurnOnDisplay()
        
    def ClearRed(self):
        
        high = self.height
        if( self.width % 8 == 0) :
            wide =  self.width // 8
        else :
            wide =  self.width // 8 + 1
        
        self.send_command(0x10) 
        for i in range(0, wide):
            self.send_data1([0xff] * high)
                
        self.send_command(0x13) 
        for i in range(0, wide):
            self.send_data1([0xff] * high)
                
        self.TurnOnDisplay()
        
    def ClearBlack(self):
        
        high = self.height
        if( self.width % 8 == 0) :
            wide =  self.width // 8
        else :
            wide =  self.width // 8 + 1
        
        self.send_command(0x10) 
        for i in range(0, wide):
            self.send_data1([0x00] * high)
                
        self.send_command(0x13) 
        for i in range(0, wide):
            self.send_data1([0x00] * high)
                
        self.TurnOnDisplay()
        
    def display(self):
        
        high = self.height
        if( self.width % 8 == 0) :
            wide =  self.width // 8
        else :
            wide =  self.width // 8 + 1
        
        # send black data
        self.send_command(0x10) 
        for i in range(0, wide):
            self.send_data1(self.buffer_black[(i * high) : ((i+1) * high)])
            
        # send red data
        self.send_command(0x13) 
        for i in range(0, wide):
            self.send_data1(self.buffer_red[(i * high) : ((i+1) * high)])
            
        self.TurnOnDisplay()
        
    def display_Base_color(self, color):
        if(self.width % 8 == 0):
            Width = self.width // 8
        else:
            Width = self.width // 8 +1
        Height = self.height
        self.send_command(0x10)   #Write Black and White image to RAM
        for j in range(Height):
            for i in range(Width):
                self.send_data(color)
                
        self.send_command(0x13)  #Write Black and White image to RAM
        for j in range(Height):
            for i in range(Width):
                self.send_data(~color)

        # self.send_command(0x12)
        # self.delay_ms(100)
        # self.WaitUntilIdle()
        
        
    def display_Partial(self, Image, Xstart, Ystart, Xend, Yend):
        if((Xstart % 8 + Xend % 8 == 8 & Xstart % 8 > Xend % 8) | Xstart % 8 + Xend % 8 == 0 | (Xend - Xstart)%8 == 0):
            Xstart = Xstart // 8 * 8
            Xend = Xend // 8 * 8
        else:
            Xstart = Xstart // 8 * 8
            if Xend % 8 == 0:
                Xend = Xend // 8 * 8
            else:
                Xend = Xend // 8 * 8 + 1
                
        Width = (Xend - Xstart) // 8
        Height = Yend - Ystart
	
        # self.send_command(0x50)
        # self.send_data(0xA9)
        # self.send_data(0x07)

        self.send_command(0x91)		#This command makes the display enter partial mode
        self.send_command(0x90)		#resolution setting
        self.send_data (Xstart//256)
        self.send_data (Xstart%256)   #x-start    

        self.send_data ((Xend-1)//256)		
        self.send_data ((Xend-1)%256)  #x-end	

        self.send_data (Ystart//256)  #
        self.send_data (Ystart%256)   #y-start    

        self.send_data ((Yend-1)//256)		
        self.send_data ((Yend-1)%256)  #y-end
        self.send_data (0x01)

        if self.partFlag == 1:
            self.partFlag = 0
            self.send_command(0x10)
            for i in range(0, Width):
                self.send_data1([0xFF] * Height)

        self.send_command(0x13)   #Write Black and White image to RAM
        for i in range(0, Width):
            self.send_data1(Image[(i * Height) : ((i+1) * Height)])

        self.send_command(0x12)
        self.delay_ms(100)
        self.WaitUntilIdle()

    def sleep(self):
        self.send_command(0x02) # power off
        self.WaitUntilIdle()
        self.send_command(0x07) # deep sleep
        self.send_data(0xa5)

def connect_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    print(f'Conectando a WiFi {ssid}...')
    wlan.connect(ssid, password)
    timeout = 20  # segundos
    for _ in range(timeout):
        if wlan.isconnected():
            print('Conectado a WiFi')
            print('IP:', wlan.ifconfig()[0])
            return True
        utime.sleep(1)
    print('No se pudo conectar a la red WiFi')
    return False


            
def draw_big_text(fb, text, x, y, scale=2, color=0):
    # fb: framebuf donde dibujar (epd.imageblack o similar)
    # text: texto a dibujar (string)
    # x, y: posición en píxeles donde empezar
    # scale: cuánto agrandar (2 = 16x16 por letra, 3=24x24, etc)
    # color: color de texto (0 o 1)

    for i, char in enumerate(text):
        # Crear un buffer temporal para el carácter (8x8)
        buf = bytearray(8)
        fb_char = framebuf.FrameBuffer(buf, 8, 8, framebuf.MONO_HLSB)
        fb_char.fill(1)  # fondo blanco
        fb_char.text(char, 0, 0, 0)  # texto negro

        # Escalar píxeles
        for row in range(8):
            for col in range(8):
                pixel = fb_char.pixel(col, row)
                if pixel == 0:  # píxel negro en texto original
                    # Dibuja un cuadrado scale x scale en fb
                    for dx in range(scale):
                        for dy in range(scale):
                            fb.pixel(x + i*8*scale + col*scale + dx, y + row*scale + dy, color)
                            
def draw_calendar(epd, year, month):
    month_names = [
    "", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
    ]

    # Limpiar buffers
    epd.imageblack.fill(0xFF)
    epd.imagered.fill(0x00)

    # Encabezado con mes y año
    title = "{} {}".format(month_names[month], year)
    epd.imageblack.text(title, 10, 10, 0x00)

    # Días de la semana
    days = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
    cell_width = 100
    cell_height = 60
    offset_x = 10
    offset_y = 40

    for i, day in enumerate(days):
        epd.imageblack.text(day, offset_x + i*cell_width + 30, offset_y, 0x00)

    # Dibuja la tabla del calendario
    cal = generate_calendar_matrix(year, month)
    for row_idx, week in enumerate(cal):
        for col_idx, day in enumerate(week):
            x = offset_x + col_idx * cell_width
            y = offset_y + 20 + row_idx * cell_height

            # Dibujar recuadro de día
            epd.imageblack.rect(x, y, cell_width, cell_height, 0x00)
            if day != 0:
                epd.imageblack.text(str(day), x + 5, y + 5, 0x00)

    epd.display()
def is_leap_year(year):
    return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)

def days_in_month(year, month):
    if month == 2:
        return 29 if is_leap_year(year) else 28
    if month in [4, 6, 9, 11]:
        return 30
    return 31

def weekday(year, month, day):
    # Zeller’s Congruence (0=Saturday, 1=Sunday, ..., 6=Friday)
    if month < 3:
        month += 12
        year -= 1
    k = year % 100
    j = year // 100
    h = (day + 13*(month + 1)//5 + k + k//4 + j//4 + 5*j) % 7
    return (h + 6) % 7  # Convert to 0=Monday, ..., 6=Sunday

def generate_calendar_matrix(year, month):
    first_weekday = weekday(year, month, 1)  # 0 = Monday
    days = days_in_month(year, month)
    calendar_matrix = []
    week = [0]*7
    day = 1

    # Fill first week
    for i in range(first_weekday, 7):
        week[i] = day
        day += 1
    calendar_matrix.append(week)

    # Fill remaining weeks
    while day <= days:
        week = [0]*7
        for i in range(7):
            if day <= days:
                week[i] = day
                day += 1
        calendar_matrix.append(week)
    return calendar_matrix
def is_leap(year):
    return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)

def days_in_month(year, month):
    days_in_months = [31, 29 if is_leap(year) else 28, 31, 30, 31, 30,
                      31, 31, 30, 31, 30, 31]
    return days_in_months[month -1]

def weekday(year, month, day):
    # Zeller's Congruence, returns 0=Monday ... 6=Sunday
    if month < 3:
        month += 12
        year -= 1
    K = year % 100
    J = year // 100
    h = (day + 13*(month + 1)//5 + K + K//4 + J//4 + 5*J) % 7
    d = (h + 6) % 7  # Convert Zeller's to 0=Monday
    return d

def monthcalendar(year, month):
    first_day = weekday(year, month, 1)  # 0=Monday
    days = days_in_month(year, month)

    weeks = []
    week = [0]*7
    day_counter = 1

    # Fill first week
    for i in range(first_day, 7):
        week[i] = day_counter
        day_counter += 1
    weeks.append(week)

    # Fill remaining weeks
    while day_counter <= days:
        week = [0]*7
        for i in range(7):
            if day_counter <= days:
                week[i] = day_counter
                day_counter += 1
        weeks.append(week)

    return weeks
def draw_calendar_quarter(epd, year, month, x0=0, y0=0):
    month_names = [
        "", "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]

    # Celdas más grandes
    cell_width = 50
    cell_height = 34
    offset_x = x0 + 10
    offset_y = y0 + 30  # Un poco más abajo para que haya espacio para el título

    # Limpiar solo zona del calendario
    epd.imageblack.fill_rect(x0, y0, 400, 240, 0xFF)
    epd.imagered.fill_rect(x0, y0, 400, 240, 0x00)

    # Título con mes y año (más grande y centrado en su zona)
    title = "{} {}".format(month_names[month], year)
    draw_big_text(epd.imageblack, title, offset_x + 60, y0 + 5, scale=2, color=0)

    # Días de la semana
    days = [ "Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"]
    for i, day in enumerate(days):
        draw_big_text(epd.imageblack, day, offset_x + i * cell_width + 5, offset_y, scale=1, color=0)

    # Generar matriz del mes con calendar
    matrix = monthcalendar(year, month)

    for row_idx, week in enumerate(matrix):
        for col_idx, day in enumerate(week):
            x = offset_x + col_idx * cell_width
            y = offset_y + 10 + row_idx * cell_height
            epd.imageblack.rect(x, y, cell_width, cell_height, 0x00)
            if day != 0:
                draw_big_text(epd.imageblack, str(day), x + 3, y + 3, scale=2, color=0)

                

    
                
def show_events_in_quadrant(epd, data, x0=400, y0=0):
    max_events = 5  # 5 eventos, cada uno ocupa 2 líneas
    line_height = 20
    offset_x = x0 + 5
    title_y = y0 + 10  # +5 píxeles más abajo
    first_event_y = title_y + 30  # separación del título a eventos

    # Limpiar zona
    epd.imageblack.fill_rect(x0, y0, 400, 240, 0xFF)
    epd.imagered.fill_rect(x0, y0, 400, 240, 0x00)

    draw_big_text(epd.imageblack, "Eventos proximos", offset_x, title_y, scale=3, color=0)

    events = data.get("items", [])
    for i, item in enumerate(events[:max_events]):
        summary = item.get("summary", "Sin título")
        start = item["start"].get("dateTime", item["start"].get("date", ""))

        # Formatear fecha y hora
        if "T" in start:
            date_part, time_part = start.split("T")
            time_part = time_part[:5]  # HH:MM
            start_display = f"{date_part} {time_part}"
        else:
            start_display = start

        y = first_event_y + i * 2 * line_height  # eventos separados por dos líneas

        # Línea 1: fecha y hora
        draw_big_text(epd.imagered, start_display, offset_x, y, scale=2, color=1)
        # Línea 2: contenido del evento
        summary_trimmed = summary if len(summary) < 45 else summary[:42] + "..."
        draw_big_text(epd.imageblack, summary_trimmed, offset_x + 10, y + line_height, scale=2, color=0)
        
def obtener_clima():
    url = ("https://api.open-meteo.com/v1/forecast?"
           "latitude=40.4168&longitude=-3.7038&"
           "current_weather=true&"
           "daily=precipitation_sum,temperature_2m_max,windspeed_10m_max&"
           "timezone=Europe%2FMadrid")

    try:
        import urequests
        respuesta = urequests.get(url)
        datos = respuesta.json()
        respuesta.close()

        # Datos actuales
        actual = datos.get("current_weather", {})
        temperatura = actual.get("temperature")               # ºC
        codigo_clima = actual.get("weathercode")              # Código del tiempo
        viento_kmh = actual.get("windspeed")                  # km/h

        # Datos diarios (primer día = hoy)
        diario = datos.get("daily", {})
        precipitacion_mm = diario.get("precipitation_sum", [None])[0]  # mm

        return temperatura, codigo_clima, viento_kmh, precipitacion_mm

    except Exception as e:
        print("Error al obtener el clima:", e)
        return None, None, None, None
    
def draw_weather_box(epd, temp_text, wind_text, rain_text, x0=0, y0=240):
    # Limpiar la zona (cuarto inferior izquierdo)
    epd.imageblack.fill_rect(x0, y0, 400, 240, 0xFF)
    epd.imagered.fill_rect(x0, y0, 400, 240, 0x00)

    # Posición reservada del icono (64x64)
    icon_x = x0 + 120
    icon_y = y0 + 120
    icon_width = 64
    icon_height = 64

    # Posición del texto a la derecha del icono
    text_x = x0 + 10
    draw_big_text(epd.imageblack, "Temp:{}C".format(temp_text), text_x, y0 + 20, scale=4, color=0)
    draw_big_text(epd.imageblack, "Wind:{}kmh".format(wind_text), text_x, y0 + 60, scale=4, color=0)
    draw_big_text(epd.imageblack, "Rain:{}mm".format(rain_text), text_x, y0 + 100, scale=4, color=0)
    
    
def obtener_tiempo_semanal():
    url = ("https://api.open-meteo.com/v1/forecast?"
           "latitude=40.4168&longitude=-3.7038&daily=temperature_2m_max,"
           "weathercode&timezone=Europe%2FMadrid")
    try:
        import urequests
        response = urequests.get(url)
        datos = response.json()
        response.close()
        dias = datos['daily']['time']
        temperaturas = datos['daily']['temperature_2m_max']
        return list(zip(dias, temperaturas))[:7]  # Solo 7 días
    except Exception as e:
        print("Error al obtener el tiempo semanal:", e)
        return []

def dibujar_histograma_vertical(epd, datos, x0=0, y0=240):

    max_temp = max(temp for _, temp in datos)
    bar_width = 40
    max_bar_height = 60
    spacing = 50
    base_y = y0 + 220  # Punto más bajo desde donde crecen las barras

    dias_semana = ["L", "M", "X", "J", "V", "S", "D"]  # Puedes usar `datetime` si prefieres

    for i, (fecha, temp) in enumerate(datos):
        altura = int((temp / max_temp) * max_bar_height)
        x = x0 + 30 + i * spacing
        y = base_y - altura

        # Dibujar barra
        epd.imagered.fill_rect(x, y, bar_width, altura, 0xFF)

        # Texto temperatura encima
        epd.imageblack.text(f"{int(temp)}", x+ 10, y - 12, 0x00)

        # Texto día debajo
        epd.imageblack.text(dias_semana[i], x + 15, base_y + 5, 0x00)


def actualizar_zona_hora(epd, ahora):
    x0, y0 = 400, 240  # Último cuadrante
    epd.imageblack.fill_rect(x0, y0, 400, 240, 0xFF)
    epd.imagered.fill_rect(x0, y0, 400, 240, 0x00)

    hora = "{:02d}:{:02d}".format(ahora[3], ahora[4])
    fecha = "{}-{:02d}-{:02d}".format(ahora[2], ahora[1], ahora[0])
    draw_big_text(epd.imageblack, "Hora actual", x0 + 10, y0 + 20, scale=2, color=0)
    draw_big_text(epd.imageblack, hora, x0 + 100, y0 + 90, scale=6, color=0)
    draw_big_text(epd.imagered, fecha, x0 + 55, y0 + 140, scale=4, color=1)
 

def main():
    if not connect_wifi(SSID, PASSWORD):
        sys.exit() 

    epd = EPD_7in5_B()
    epd.init()
    epd.Clear()    
  
    t = utime.localtime()
    year = t[0]
    month = t[1]

    draw_calendar_quarter(epd, year, month, x0=0, y0=0)

    
    now = "{}-{:02d}-{:02d}T00:00:00Z".format(year, month, t[2])
    url = ("https://www.googleapis.com/calendar/v3/calendars/"
           "mail/events?"
           "key=KEY"
           "timeMin={}&singleEvents=true&orderBy=startTime").format(now)

    try:
        response = urequests.get(url)
        data = response.json()
        response.close()
    except Exception as e:
        print("Error al cargar eventos:", e)
        data = {"items": []}
        epd.imageblack.text("Error al cargar eventos", 410, 10, 0x00)

    show_events_in_quadrant(epd, data, x0=400, y0=0)
    temperatura, codigo_clima, viento_kmh, precipitacion_mm = obtener_clima()
    draw_weather_box(epd, temperatura, viento_kmh,precipitacion_mm)
    ahora = utime.localtime()
    datos_tiempo = obtener_tiempo_semanal()
    dibujar_histograma_vertical(epd, datos_tiempo, x0=0, y0=240)
    actualizar_zona_hora(epd, ahora)
    epd.display()

    epd.delay_ms(10000)
    epd.sleep()

if __name__ == '__main__':
    main()

 
