import mysql.connector
from config.database import get_db_connection

def init_database():
    print("Connecting to database to initialize schema...")
    conn = get_db_connection()
    if not conn:
        print("Could not establish connection. Check your .env credentials.")
        return

    cursor = conn.cursor()
    try:
        # 1. GAMBLERS (Base Table)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS GAMBLERS (
                gambler_id BIGINT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(255) UNIQUE NOT NULL,
                full_name VARCHAR(255),
                email VARCHAR(255) UNIQUE,
                is_active BOOLEAN DEFAULT TRUE,
                initial_stake DECIMAL(10,2) NOT NULL,
                current_stake DECIMAL(10,2) NOT NULL,
                win_threshold DECIMAL(10,2) NOT NULL,
                loss_threshold DECIMAL(10,2) NOT NULL,
                min_required_stake DECIMAL(10,2) NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        """)

        # 2. BETTING_PREFERENCES (Depends on GAMBLERS)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS BETTING_PREFERENCES (
                preference_id BIGINT AUTO_INCREMENT PRIMARY KEY,
                gambler_id BIGINT UNIQUE NOT NULL,
                min_bet DECIMAL(10,2) NOT NULL,
                max_bet DECIMAL(10,2) NOT NULL,
                preferred_game_type VARCHAR(100) DEFAULT 'ALL',
                auto_play_enabled BOOLEAN DEFAULT FALSE,
                auto_play_max_games INT DEFAULT 0,
                session_loss_limit DECIMAL(10,2),
                session_win_target DECIMAL(10,2),
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (gambler_id) REFERENCES GAMBLERS(gambler_id) ON DELETE CASCADE
            )
        """)

        # 3. BETTING_STRATEGIES (Standalone Reference Table)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS BETTING_STRATEGIES (
                strategy_id TINYINT AUTO_INCREMENT PRIMARY KEY,
                strategy_code VARCHAR(50) UNIQUE NOT NULL,
                strategy_name VARCHAR(100) NOT NULL,
                strategy_type ENUM('FIXED', 'MARTINGALE', 'FIBONACCI', 'PERCENTAGE', 'CUSTOM') NOT NULL,
                is_progressive BOOLEAN DEFAULT FALSE,
                is_active BOOLEAN DEFAULT TRUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 4. ODDS_CONFIGURATIONS (Standalone Reference Table)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ODDS_CONFIGURATIONS (
                odds_config_id BIGINT AUTO_INCREMENT PRIMARY KEY,
                odds_type ENUM('FIXED', 'PROBABILITY', 'AMERICAN', 'DECIMAL') NOT NULL,
                fixed_multiplier DECIMAL(10,4),
                american_odds INT,
                decimal_odds DECIMAL(10,4),
                probability_payout_factor DECIMAL(10,4),
                house_edge DECIMAL(5,4) DEFAULT 0.0000,
                is_default BOOLEAN DEFAULT FALSE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 5. SESSIONS (Depends on GAMBLERS)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS SESSIONS (
                session_id BIGINT AUTO_INCREMENT PRIMARY KEY,
                gambler_id BIGINT NOT NULL,
                status ENUM('ACTIVE', 'PAUSED', 'COMPLETED', 'TERMINATED') DEFAULT 'ACTIVE',
                end_reason ENUM('WIN_LIMIT', 'LOSS_LIMIT', 'MANUAL', 'TIMEOUT', 'ERROR'),
                starting_stake DECIMAL(10,2) NOT NULL,
                ending_stake DECIMAL(10,2),
                peak_stake DECIMAL(10,2),
                lowest_stake DECIMAL(10,2),
                max_games INT,
                games_played INT DEFAULT 0,
                total_pause_seconds INT DEFAULT 0,
                started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                ended_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (gambler_id) REFERENCES GAMBLERS(gambler_id) ON DELETE CASCADE
            )
        """)

        # 6. SESSION_PARAMETERS (Depends on SESSIONS)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS SESSION_PARAMETERS (
                parameter_id BIGINT AUTO_INCREMENT PRIMARY KEY,
                session_id BIGINT UNIQUE NOT NULL,
                lower_limit DECIMAL(10,2) NOT NULL,
                upper_limit DECIMAL(10,2) NOT NULL,
                min_bet DECIMAL(10,2) NOT NULL,
                max_bet DECIMAL(10,2) NOT NULL,
                default_win_probability DECIMAL(5,4) DEFAULT 0.5000,
                max_session_minutes INT,
                strict_mode BOOLEAN DEFAULT TRUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES SESSIONS(session_id) ON DELETE CASCADE
            )
        """)

        # 7. PAUSE_RECORDS (Depends on SESSIONS)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS PAUSE_RECORDS (
                pause_id BIGINT AUTO_INCREMENT PRIMARY KEY,
                session_id BIGINT NOT NULL,
                pause_reason VARCHAR(255),
                paused_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                resumed_at DATETIME,
                pause_seconds INT,
                FOREIGN KEY (session_id) REFERENCES SESSIONS(session_id) ON DELETE CASCADE
            )
        """)

        # 8. BETS (Depends on SESSIONS, GAMBLERS, BETTING_STRATEGIES)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS BETS (
                bet_id BIGINT AUTO_INCREMENT PRIMARY KEY,
                session_id BIGINT NOT NULL,
                gambler_id BIGINT NOT NULL,
                strategy_id TINYINT,
                game_index INT NOT NULL,
                bet_amount DECIMAL(10,2) NOT NULL,
                win_probability DECIMAL(5,4) NOT NULL,
                odds_type ENUM('FIXED', 'PROBABILITY', 'AMERICAN', 'DECIMAL') NOT NULL,
                odds_value DECIMAL(10,4) NOT NULL,
                potential_win DECIMAL(10,2) NOT NULL,
                stake_before DECIMAL(10,2) NOT NULL,
                stake_after DECIMAL(10,2) NOT NULL,
                is_settled BOOLEAN DEFAULT FALSE,
                placed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES SESSIONS(session_id) ON DELETE CASCADE,
                FOREIGN KEY (gambler_id) REFERENCES GAMBLERS(gambler_id) ON DELETE CASCADE,
                FOREIGN KEY (strategy_id) REFERENCES BETTING_STRATEGIES(strategy_id) ON DELETE SET NULL
            )
        """)

        # 9. GAME_RECORDS (Depends on SESSIONS, BETS, ODDS_CONFIGURATIONS)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS GAME_RECORDS (
                game_id BIGINT AUTO_INCREMENT PRIMARY KEY,
                session_id BIGINT NOT NULL,
                bet_id BIGINT UNIQUE NOT NULL,
                odds_config_id BIGINT,
                outcome ENUM('WIN', 'LOSS', 'PUSH') NOT NULL,
                payout_amount DECIMAL(10,2) DEFAULT 0.00,
                loss_amount DECIMAL(10,2) DEFAULT 0.00,
                net_change DECIMAL(10,2) NOT NULL,
                stake_before DECIMAL(10,2) NOT NULL,
                stake_after DECIMAL(10,2) NOT NULL,
                consecutive_win_streak INT DEFAULT 0,
                consecutive_loss_streak INT DEFAULT 0,
                game_duration_ms INT,
                resolved_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES SESSIONS(session_id) ON DELETE CASCADE,
                FOREIGN KEY (bet_id) REFERENCES BETS(bet_id) ON DELETE CASCADE,
                FOREIGN KEY (odds_config_id) REFERENCES ODDS_CONFIGURATIONS(odds_config_id) ON DELETE SET NULL
            )
        """)

        # 10. STAKE_TRANSACTIONS (Depends on GAMBLERS, SESSIONS, BETS, GAME_RECORDS)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS STAKE_TRANSACTIONS (
                transaction_id BIGINT AUTO_INCREMENT PRIMARY KEY,
                session_id BIGINT NULL,
                gambler_id BIGINT NOT NULL,
                bet_id BIGINT NULL,
                game_id BIGINT NULL,
                transaction_type ENUM('INITIAL_STAKE', 'BET_PLACED', 'BET_WIN', 'BET_LOSS', 'DEPOSIT', 'WITHDRAWAL', 'ADJUSTMENT', 'RESET') NOT NULL,
                amount DECIMAL(10,2) NOT NULL,
                balance_before DECIMAL(10,2) NOT NULL,
                balance_after DECIMAL(10,2) NOT NULL,
                transaction_ref VARCHAR(255),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (gambler_id) REFERENCES GAMBLERS(gambler_id) ON DELETE CASCADE,
                FOREIGN KEY (session_id) REFERENCES SESSIONS(session_id) ON DELETE CASCADE,
                FOREIGN KEY (bet_id) REFERENCES BETS(bet_id) ON DELETE SET NULL,
                FOREIGN KEY (game_id) REFERENCES GAME_RECORDS(game_id) ON DELETE SET NULL
            )
        """)

        # 11. RUNNING_TOTALS_SNAPSHOTS (Depends on SESSIONS, GAME_RECORDS)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS RUNNING_TOTALS_SNAPSHOTS (
                snapshot_id BIGINT AUTO_INCREMENT PRIMARY KEY,
                session_id BIGINT NOT NULL,
                game_id BIGINT NOT NULL,
                total_games INT DEFAULT 0,
                total_wins INT DEFAULT 0,
                total_losses INT DEFAULT 0,
                total_pushes INT DEFAULT 0,
                total_winnings DECIMAL(10,2) DEFAULT 0.00,
                total_losses_amount DECIMAL(10,2) DEFAULT 0.00,
                net_profit DECIMAL(10,2) DEFAULT 0.00,
                win_rate DECIMAL(5,4) DEFAULT 0.0000,
                profit_factor DECIMAL(10,4) DEFAULT 0.0000,
                roi DECIMAL(10,4) DEFAULT 0.0000,
                longest_win_streak INT DEFAULT 0,
                longest_loss_streak INT DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES SESSIONS(session_id) ON DELETE CASCADE,
                FOREIGN KEY (game_id) REFERENCES GAME_RECORDS(game_id) ON DELETE CASCADE
            )
        """)

        # 12. VALIDATION_EVENTS (Depends on SESSIONS, GAMBLERS)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS VALIDATION_EVENTS (
                validation_id BIGINT AUTO_INCREMENT PRIMARY KEY,
                session_id BIGINT NULL,
                gambler_id BIGINT NULL,
                error_type ENUM('STAKE_ERROR', 'BET_ERROR', 'LIMIT_ERROR', 'SYSTEM_ERROR') NOT NULL,
                severity ENUM('WARNING', 'CRITICAL') NOT NULL,
                field_name VARCHAR(100),
                attempted_value VARCHAR(255),
                message TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES SESSIONS(session_id) ON DELETE CASCADE,
                FOREIGN KEY (gambler_id) REFERENCES GAMBLERS(gambler_id) ON DELETE CASCADE
            )
        """)

        conn.commit()
        print("Database schema initialized successfully! All 12 tables created.")

    except mysql.connector.Error as err:
        print(f"error initializing database: {err}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    init_database()