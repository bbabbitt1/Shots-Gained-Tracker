import sqlite3

# --- CONFIG ---
db_path = "shots_gained.db"

# --- CONNECT ---
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# --- CREATE TABLE ---
cursor.execute("""
CREATE TABLE IF NOT EXISTS DimRound (
    RoundID INTEGER PRIMARY KEY AUTOINCREMENT,
    PlayerID INTEGER NOT NULL,
    CoursePlayed TEXT,
    RoundDate TEXT,
    HolesPlayed INTEGER,
    TeePreference TEXT,
    CreatedDate DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (PlayerID) REFERENCES DimPlayer(PlayerID)
);
""")

conn.commit()
conn.close()

print("✅ DimRound table created successfully.")
