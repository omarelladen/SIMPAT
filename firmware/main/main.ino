// Copyright 2026 Omar Zagonel El Laden
// SPDX-License-Identifier: GPL-2.0-only

#include <sys/time.h>
#include <WiFi.h>
#include <HTTPClient.h>


#define DEBUG false
#if DEBUG
    #define PRINT(x)        Serial.print(x)
    #define PRINTLN(x)      Serial.println(x)
    #define SERIAL_BEGIN(r) Serial.begin(r)
    #define DELAY(t)        delay(t)
    #define SERIAL_FLUSH()  Serial.flush()
#else
    #define PRINT(x)
    #define PRINTLN(x)
    #define SERIAL_BEGIN(r)
    #define DELAY(t)
    #define SERIAL_FLUSH()
#endif

#define S3 true
#if S3  // Waveshare ESP32-S3-Zero
    #define PIN_WAKEUP 4
    #define PIN_LED 7
    #define PIN_BUZZER 6
    #define PIN_BATTERY 8
#else   // DOIT ESP32 DEVKIT V1
    #define PIN_WAKEUP 4
    #define PIN_LED 23
    #define PIN_BUZZER 22
    #define PIN_BATTERY 34
#endif

#define WAKEUP_LEVEL HIGH

#define MAX_TIME_REP_S 10
#define ALERT_REP_COUNT 10

#define NUM_POST_TRIES 10
#define TIMEOUT_WIFI_S 30
#define NW_CHECK_DELAY 300
#define NEXT_RETRY_MINUTES 30

#define NUM_BEEPS 3
#define BEEP_DELAY 200

#define SLEEP_DELAY 300

#define BAUD_RATE 115200

#define NEXT_WAKEUP_FIELD "\"next_wakeup\":"

#define NW_SSID ""
#define NW_PASSWORD ""

#define URL "http://192.168.100.40:8000/alert"

#define ITEM_ID 0

// TODO: use vars instead of defines to change based on server response


RTC_DATA_ATTR int boot_count = 0;
RTC_DATA_ATTR int rep_wakeups = 0;
RTC_DATA_ATTR time_t last_time_awake = 0;
RTC_DATA_ATTR bool timout_risk = false;


void beep_buzzer()
{
    for (int i=0; i < NUM_BEEPS; i++)
    {
        digitalWrite(PIN_BUZZER, HIGH);
        delay(BEEP_DELAY);
        digitalWrite(PIN_BUZZER, LOW);
        delay(BEEP_DELAY);
    }
}

bool connect_wifi(time_t *time_now)
{
    if (WiFi.status() != WL_CONNECTED)
    {
        WiFi.begin(NW_SSID, NW_PASSWORD);

        time(time_now);
        time_t time_start = *time_now;

        PRINTLN("Connecting");
        while(WiFi.status() != WL_CONNECTED)
        {
            delay(NW_CHECK_DELAY);
            PRINT(".");

            time(time_now);
            if (*time_now - time_start > TIMEOUT_WIFI_S)
            {
                PRINTLN("Timeout");
                return false;
            }
        }
    }

    PRINTLN("Connected");
    PRINT("IP: ");
    PRINTLN(WiFi.localIP());

    return true;
}

int get_json_value(String response, String field)
{
    int pos_init_field = response.indexOf(field);
    if (pos_init_field != -1)
    {
        int pos_init_value = pos_init_field + field.length();

        int pos_end_value = response.indexOf(",", pos_init_value);
        if (pos_end_value == -1)
            pos_end_value = response.indexOf("}", pos_init_value);

        if (pos_end_value != -1)
        {
            String field_value = response.substring(pos_init_value, pos_end_value);
            field_value.trim();

            int next_wakeup = field_value.toInt();

            PRINT("found value ");
            PRINT(next_wakeup);
            PRINT(" for field ");
            PRINTLN(field);

            return next_wakeup;
        }
    }

    PRINT(field);
    PRINTLN(" not found");
    return -1;
}

bool post_data(int battery_level, String status)
{
    for (int i=0; i < NUM_POST_TRIES; i++)
    {
        PRINTLN("Will try to POST");

        if (WiFi.status() == WL_CONNECTED)
        {
            HTTPClient http;
            http.begin(URL);

            String body =
                "{\"item_id\":"      + String(ITEM_ID)          + "," \
                + "\"status\":"      + "\"" + status + "\""     + "," \
                + "\"battery\":"     + String(battery_level)    + "," \
                + "\"boot_count\":"  + String(boot_count)       + "," \
                + "\"rep_wakeups\":" + String(rep_wakeups) + "," \
                + "\"bssid\":"       + "\"" + WiFi.BSSIDstr() + "\""  \
                + "}";

            http.addHeader("Content-Type", "application/json");

            PRINTLN("POSTing");
            int http_response_code = http.POST(body);

            if (http_response_code > 0)
            {
                String response = http.getString();

                PRINTLN("Success sending POST");
                PRINT("Response code: ");
                PRINTLN(http_response_code);
                PRINT("Response: ");
                PRINTLN(response);

                int next_wakeup = get_json_value(response, NEXT_WAKEUP_FIELD);
                if (next_wakeup > 0)
                {
                    esp_sleep_enable_timer_wakeup(next_wakeup * 1000000);  // s
                }
                else
                {
                    PRINTLN("Invalid value for next_wakeup");
                }

                http.end();
                return true;
            }

            PRINTLN("Error sending POST");
            PRINT("Response code: ");
            PRINTLN(http_response_code);

            http.end();
        }
        else
        {
            PRINTLN("Error in connection");
        }
    }

    return false;
}

void setup()
{
    SERIAL_BEGIN(BAUD_RATE);
    DELAY(1500);

    pinMode(PIN_WAKEUP, INPUT_PULLUP);
    pinMode(PIN_LED,    OUTPUT);
    pinMode(PIN_BUZZER, OUTPUT);


    esp_sleep_wakeup_cause_t wakeup_cause = esp_sleep_get_wakeup_cause();

    esp_sleep_enable_ext0_wakeup((gpio_num_t)PIN_WAKEUP, WAKEUP_LEVEL);


    boot_count++;
    PRINT("Boot num: ");
    PRINTLN(boot_count);

    // Read battery level
    int battery_level = analogRead(PIN_BATTERY);
    PRINT("Battery: ");
    PRINTLN(battery_level);


    time_t time_now;
    time(&time_now);

    time_t time_diff = time_now - last_time_awake;

    PRINT("Time: ");
    PRINTLN(time_now);
    PRINT("Last time awake: ");
    PRINTLN(last_time_awake);
    PRINT("Diff: ");
    PRINTLN(time_diff);



    if (boot_count == 1)
    {
        if (connect_wifi(&time_now))
            post_data(battery_level, "reset");
    }

    if (wakeup_cause == ESP_SLEEP_WAKEUP_TIMER && !timout_risk)
    {
        if (connect_wifi(&time_now))
            post_data(battery_level, "ping");
    }

    if (timout_risk)
    {
        if (connect_wifi(&time_now))
            if (post_data(battery_level, "timeout_risk"))
                timout_risk = false;
    }

    if (time_diff < MAX_TIME_REP_S)
    {
        rep_wakeups++;
        PRINT("Repeated wakeup! Count: ");
        PRINTLN(rep_wakeups);
    }
    else
    {
        // Reset count
        rep_wakeups = 1;
        PRINTLN("Normal wakeup");
    }

    if (rep_wakeups > ALERT_REP_COUNT)  // TODO: debounce (now using SLEEP_DELAY)
    {
        beep_buzzer();

        if (connect_wifi(&time_now))
        {
            if (!post_data(battery_level, "risk"))
                timout_risk = true;
                esp_sleep_enable_timer_wakeup(NEXT_RETRY_MINUTES*60*1000000);
        }
        else
        {
            timout_risk = true;
            esp_sleep_enable_timer_wakeup(NEXT_RETRY_MINUTES*60*1000000);
        }
    }


    digitalWrite(PIN_LED, HIGH);

    delay(SLEEP_DELAY);

    PRINTLN("Going to sleep now");
    SERIAL_FLUSH();

    time(&time_now);
    last_time_awake = time_now;

    // Sleep
    esp_deep_sleep_start();
}

void loop()
{
    // not called
}
