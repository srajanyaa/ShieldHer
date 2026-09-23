/*
 * shieldHer Safety Analyzer
 * Analyzes safety inputs and generates risk assessment
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <time.h>

#define MAX_LINE 512
#define MAX_ADVICE 1024

/* Parse KEY=VALUE from input file */
int parse_key_value(const char *line, char *key, int *value) {
    char *eq;
    eq = strchr(line, '=');
    if (eq == NULL) return 0;
    
    size_t key_len = eq - line;
    strncpy(key, line, key_len);
    key[key_len] = '\0';
    
    *value = atoi(eq + 1);
    return 1;
}

/* Trim whitespace from string */
char *trim(char *str) {
    while (isspace((unsigned char)*str)) str++;
    
    if (*str == 0) return str;
    
    char *end = str + strlen(str) - 1;
    while (end > str && isspace((unsigned char)*end)) end--;
    
    *(end + 1) = '\0';
    return str;
}

/* Read full line into buffer (handles multiline NOTES) */
void read_input_file(const char *filename,
                     int *q_isolated, int *q_poor_lighting, int *q_late_night,
                     int *q_followed, int *q_low_battery, int *q_crowded,
                     int *confidence, int *timer_seconds, int *timer_minutes, int *timer_expired,
                     char *notes, size_t notes_size) {
    FILE *fp = fopen(filename, "r");
    if (fp == NULL) {
        perror("Error opening input file");
        exit(1);
    }
    
    char line[MAX_LINE];
    char key[64];
    int value;
    
    /* Reset notes */
    notes[0] = '\0';
    /* Initialize timer_seconds to -1 to indicate not set */
    *timer_seconds = -1;
    
    while (fgets(line, sizeof(line), fp) != NULL) {
        /* Remove newline */
        line[strcspn(line, "\n")] = 0;
        
        if (parse_key_value(line, key, &value)) {
            if (strcmp(key, "Q_ISOLATED") == 0) *q_isolated = value;
            else if (strcmp(key, "Q_POOR_LIGHTING") == 0) *q_poor_lighting = value;
            else if (strcmp(key, "Q_LATE_NIGHT") == 0) *q_late_night = value;
            else if (strcmp(key, "Q_FOLLOWED") == 0) *q_followed = value;
            else if (strcmp(key, "Q_LOW_BATTERY") == 0) *q_low_battery = value;
            else if (strcmp(key, "Q_CROWDED") == 0) *q_crowded = value;
            else if (strcmp(key, "CONFIDENCE") == 0) *confidence = value;
            else if (strcmp(key, "TIMER_SECONDS") == 0) *timer_seconds = value;
            else if (strcmp(key, "TIMER_MINUTES") == 0) *timer_minutes = value;
            else if (strcmp(key, "TIMER_EXPIRED") == 0) *timer_expired = value;
            else if (strcmp(key, "NOTES") == 0) {
                strncpy(notes, line + strlen("NOTES="), notes_size - 1);
                notes[notes_size - 1] = '\0';
            }
        }
    }
    
    fclose(fp);
}

/* Write output file */
void write_output_file(const char *filename, int risk_score, const char *risk_level,
                       const char *trend, int sos_needed, const char *advice) {
    FILE *fp = fopen(filename, "w");
    if (fp == NULL) {
        perror("Error opening output file");
        exit(1);
    }
    
    fprintf(fp, "RISK_SCORE=%d\n", risk_score);
    fprintf(fp, "RISK_LEVEL=%s\n", risk_level);
    fprintf(fp, "TREND=%s\n", trend);
    fprintf(fp, "SOS_NEEDED=%d\n", sos_needed);
    fprintf(fp, "ADVICE=%s\n", advice);
    
    fclose(fp);
}

/* Get current timestamp as string */
void get_timestamp(char *buffer, size_t size) {
    time_t now = time(NULL);
    struct tm *tm_info = localtime(&now);
    strftime(buffer, size, "%Y-%m-%d %H:%M:%S", tm_info);
}

/* Read history and compute trend */
void compute_trend(const char *history_file, char *trend) {
    FILE *fp = fopen(history_file, "r");
    
    if (fp == NULL) {
        /* No history, assume stable */
        strcpy(trend, "stable");
        return;
    }
    
    int scores[10];
    int count = 0;
    char line[MAX_LINE];
    
    /* Skip header */
    fgets(line, sizeof(line), fp);
    
    /* Read last 10 scores */
    while (fgets(line, sizeof(line), fp) != NULL && count < 10) {
        char *token = strtok(line, ",");
        if (token != NULL) {
            /* Skip timestamp */
            token = strtok(NULL, ",");
            if (token != NULL) {
                scores[count++] = atoi(token);
            }
        }
    }
    fclose(fp);
    
    if (count < 2) {
        strcpy(trend, "stable");
        return;
    }
    
    /* Calculate averages of recent vs older scores */
    int recent_count = (count + 1) / 2;
    int older_count = count / 2;
    
    double recent_avg = 0;
    double older_avg = 0;
    
    for (int i = 0; i < recent_count; i++) {
        recent_avg += scores[count - 1 - i];
    }
    recent_avg /= recent_count;
    
    for (int i = 0; i < older_count; i++) {
        older_avg += scores[i];
    }
    older_avg /= older_count;
    
    /* Determine trend */
    double diff = recent_avg - older_avg;
    if (diff < -5) {
        strcpy(trend, "improving");
    } else if (diff > 5) {
        strcpy(trend, "worsening");
    } else {
        strcpy(trend, "stable");
    }
}

/* Append to history CSV */
void append_history(const char *history_file, int risk_score, const char *risk_level,
                    int confidence, int timer_expired, const char *notes) {
    FILE *fp = fopen(history_file, "a");
    if (fp == NULL) {
        perror("Error opening history file");
        exit(1);
    }
    
    /* Check if file is empty to write header */
    fseek(fp, 0, SEEK_END);
    long pos = ftell(fp);
    
    if (pos == 0) {
        fprintf(fp, "timestamp,risk_score,risk_level,confidence,timer_expired,notes\n");
    }
    
    char timestamp[64];
    get_timestamp(timestamp, sizeof(timestamp));
    
    /* Escape notes (simple CSV escaping) */
    fprintf(fp, "%s,%d,%s,%d,%d,\"%s\"\n",
            timestamp, risk_score, risk_level, confidence, timer_expired, notes);
    
    fclose(fp);
}

/* Read contacts and generate SOS draft */
void generate_sos_draft(const char *contacts_file, const char *sos_file,
                         int risk_score, const char *risk_level,
                         int q_followed, int q_isolated, const char *notes) {
    FILE *c_fp = fopen(contacts_file, "r");
    FILE *s_fp = fopen(sos_file, "w");
    
    if (c_fp == NULL || s_fp == NULL) {
        if (c_fp) fclose(c_fp);
        if (s_fp) fclose(s_fp);
        return;
    }
    
    fprintf(s_fp, "=== EMERGENCY SOS DRAFT ===\n\n");
    fprintf(s_fp, "Risk Assessment: %s (Score: %d/100)\n\n", risk_level, risk_score);
    
    fprintf(s_fp, "Immediate Concerns:\n");
    if (q_followed) fprintf(s_fp, "  - Someone may be following me\n");
    if (q_isolated) fprintf(s_fp, "  - I am in an isolated area\n");
    fprintf(s_fp, "\n");
    
    if (strlen(notes) > 0) {
        fprintf(s_fp, "My Notes:\n%s\n\n", notes);
    }
    
    fprintf(s_fp, "Suggested Message to Send:\n");
    fprintf(s_fp, "---\n");
    fprintf(s_fp, "I am not feeling safe right now. ");
    fprintf(s_fp, "My current risk level is %s. ", risk_level);
    fprintf(s_fp, "Please check on me or call authorities if I don't respond soon.\n");
    fprintf(s_fp, "---\n\n");
    
    fprintf(s_fp, "Trusted Contacts:\n");
    
    char line[MAX_LINE];
    while (fgets(line, sizeof(line), c_fp) != NULL) {
        line[strcspn(line, "\n")] = 0;
        
        char *name = strtok(line, ",");
        char *phone = strtok(NULL, ",");
        char *email = strtok(NULL, ",");
        char *relation = strtok(NULL, ",");
        
        if (name && phone) {
            fprintf(s_fp, "  - %s (%s): %s", name, relation ? relation : "Contact", phone);
            if (email) fprintf(s_fp, ", %s", email);
            fprintf(s_fp, "\n");
        }
    }
    
    fprintf(s_fp, "\nPlease take action to help me stay safe.\n");
    
    fclose(c_fp);
    fclose(s_fp);
}

/* Generate advice based on risk factors */
void generate_advice(int q_isolated, int q_poor_lighting, int q_late_night,
                     int q_followed, int q_low_battery, int q_crowded,
                     int timer_expired, char *advice, size_t advice_size) {
    if (advice_size == 0) return;
    advice[0] = '\0';
    char *separator = "";
    int pos = 0;
    
    /* Helper to append advice */
    #define APPEND(fmt, ...) pos += snprintf(advice + pos, advice_size - pos, "%s" fmt, separator, ##__VA_ARGS__); \
                             separator = "; "
    
    /* Battery warning first */
    if (q_low_battery) {
        APPEND("Charge your phone immediately or move to a location with power");
    }
    
    /* Being followed - highest priority */
    if (q_followed) {
        APPEND("URGENT: If followed, go to nearest public place and call someone you trust");
        APPEND("Consider calling campus security or police if danger feels immediate");
    }
    
    /* Isolation and lighting */
    if (q_isolated && q_poor_lighting) {
        APPEND("Move to a well-lit, populated area as soon as possible");
    } else if (q_isolated) {
        APPEND("Try to reach a more populated area; stay aware of your surroundings");
    } else if (q_poor_lighting) {
        APPEND("Seek better lighting; stay in areas with visible activity");
    }
    
    /* Late night specific advice */
    if (q_late_night) {
        APPEND("Stay on well-traveled paths; consider calling a friend to stay on the phone");
        if (!q_crowded) {
            APPEND("Avoid shortcuts through isolated areas");
        }
    }
    
    /* Crowded but non-protective */
    if (q_crowded) {
        APPEND("Crowds can be unpredictable; identify safe exits and stay alert");
    }
    
    /* Timer expired */
    if (timer_expired) {
        APPEND("Check-in timer expired - contact your trusted person now");
    }
    
    /* Low confidence multiplier warning */
    /* (confidence is already factored into score, but give general advice) */
    
    /* Default safe advice */
    if (advice[0] == '\0') {
        APPEND("Stay aware of your surroundings; trust your instincts");
    }
    
    #undef APPEND
}

/* Get risk level string from score */
const char *get_risk_level(int score) {
    if (score <= 25) return "low";
    if (score <= 50) return "medium";
    if (score <= 75) return "high";
    return "critical";
}

int main(int argc, char *argv[]) {
    /* Input/output file paths */
    const char *input_file = "data/input.txt";
    const char *output_file = "data/output.txt";
    const char *history_file = "data/history.csv";
    const char *contacts_file = "data/contacts.txt";
    const char *sos_file = "data/sos_draft.txt";
    
    /* Parse command line args for custom paths (optional) */
    for (int i = 1; i < argc; i += 2) {
        if (i + 1 < argc) {
            if (strcmp(argv[i], "-i") == 0) input_file = argv[i + 1];
            else if (strcmp(argv[i], "-o") == 0) output_file = argv[i + 1];
            else if (strcmp(argv[i], "-h") == 0) history_file = argv[i + 1];
            else if (strcmp(argv[i], "-c") == 0) contacts_file = argv[i + 1];
            else if (strcmp(argv[i], "-s") == 0) sos_file = argv[i + 1];
        }
    }
    
    /* Variables for parsed input */
    int q_isolated = 0, q_poor_lighting = 0, q_late_night = 0;
    int q_followed = 0, q_low_battery = 0, q_crowded = 0;
    int confidence = 3, timer_seconds = -1, timer_minutes = 30, timer_expired = 0;
    char notes[MAX_LINE] = "";
    
    /* Read input file */
    read_input_file(input_file,
                    &q_isolated, &q_poor_lighting, &q_late_night,
                    &q_followed, &q_low_battery, &q_crowded,
                    &confidence, &timer_seconds, &timer_minutes, &timer_expired,
                    notes, sizeof(notes));
    
    /* Calculate base score */
    int base_score = 0;
    if (q_isolated) base_score += 20;
    if (q_poor_lighting) base_score += 15;
    if (q_late_night) base_score += 20;
    if (q_followed) base_score += 25;
    if (q_low_battery) base_score += 10;
    if (q_crowded) base_score += 15;
    
    /* Apply timer adjustment based on seconds (with minutes fallback) */
    if (timer_seconds >= 0) {
        /* Second-based scoring: 10-59sec +15, 60-120sec +10, 121-300sec +5, 301-600sec +0 */
        if (timer_seconds >= 10 && timer_seconds <= 59) base_score += 15;
        else if (timer_seconds >= 60 && timer_seconds <= 120) base_score += 10;
        else if (timer_seconds >= 121 && timer_seconds <= 300) base_score += 5;
        /* 301-600 seconds: +0 (no bonus) */
    } else {
        /* Fallback to minutes-based scoring for backward compatibility */
        if (timer_minutes == 10) base_score += 10;
        else if (timer_minutes == 20) base_score += 5;
    }
    
    /* Apply timer expired penalty */
    if (timer_expired) base_score += 20;
    
    /* Apply confidence multiplier */
    double multiplier;
    switch (confidence) {
        case 1: multiplier = 1.5; break;
        case 2: multiplier = 1.25; break;
        case 3: multiplier = 1.0; break;
        case 4: multiplier = 0.85; break;
        case 5: multiplier = 0.7; break;
        default: multiplier = 1.0;
    }
    
    int risk_score = (int)(base_score * multiplier);
    
    /* Clamp to 0-100 */
    if (risk_score < 0) risk_score = 0;
    if (risk_score > 100) risk_score = 100;
    
    /* Get risk level */
    const char *risk_level = get_risk_level(risk_score);
    
    /* Compute trend from history */
    char trend[32];
    compute_trend(history_file, trend);
    
    /* Determine if SOS is needed */
    int sos_needed = (risk_score >= 50) ? 1 : 0;
    
    /* Generate advice */
    char advice[MAX_ADVICE];
    generate_advice(q_isolated, q_poor_lighting, q_late_night,
                    q_followed, q_low_battery, q_crowded,
                    timer_expired, advice, sizeof(advice));
    
    /* Write output file */
    write_output_file(output_file, risk_score, risk_level, trend, sos_needed, advice);
    
    /* Append to history */
    append_history(history_file, risk_score, risk_level, confidence, timer_expired, notes);
    
    /* Generate SOS draft if needed */
    if (sos_needed) {
        generate_sos_draft(contacts_file, sos_file, risk_score, risk_level,
                          q_followed, q_isolated, notes);
    }
    
    return 0;
}
