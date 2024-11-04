import psycopg2
import os


class SQLManager(object):

    # Use the following code to reset the database:
    # # truncate table_propositions cascade;
    # # ALTER SEQUENCE table_propositions_id_seq RESTART;

    def __init__(self):
        # Get PostgreSQL credentials from environment variables
        self._db_host = os.getenv('DB_HOST')
        self._db_name = os.getenv('DB_NAME')
        self._db_user = os.getenv('DB_USER')
        self._db_password = os.getenv('DB_PASSWORD')
        self._db_port = os.getenv('DB_PORT', '5432')
        self._schema = os.getenv('DB_SCHEMA', 'public')

    def get_db_connection(self):
        # Initialize the PostgreSQL connection
        return psycopg2.connect(
            host=self._db_host,
            dbname=self._db_name,
            user=self._db_user,
            password=self._db_password,
            port=self._db_port,
            options=f'-c search_path={self._schema}'
        )

    def create_tables(self):
        # Create table propositions table if it doesn't exist
        conn = self.get_db_connection()
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS table_propositions (
                        id SERIAL PRIMARY KEY,
                        game_name TEXT,
                        max_players INTEGER,
                        date DATE,
                        time TIME,
                        duration INTEGER,
                        notes TEXT,
                        bgg_game_id INTEGER, 
                        proposed_by TEXT,
                        creation_timestamp_tz timestamptz NULL DEFAULT now()
                    )''')

        c.execute('''CREATE TABLE IF NOT EXISTS joined_players (
                        id SERIAL PRIMARY KEY,
                        table_id INTEGER REFERENCES table_propositions(id) ON DELETE CASCADE,
                        player_name TEXT,
                        creation_timestamp_tz timestamptz NULL DEFAULT now(),
                        UNIQUE(table_id, player_name)
                    )''')

        c.execute('''CREATE TABLE IF NOT EXISTS users (
                        email TEXT PRIMARY KEY,
                        username TEXT,
                        is_admin BOOLEAN DEFAULT FALSE)
                    ''')

        c.execute('''CREATE OR REPLACE FUNCTION check_max_players()
                     RETURNS trigger
                     LANGUAGE plpgsql
                    AS $function$
                        DECLARE
                            current_player_count INTEGER;
                            max_players_allowed INTEGER;
                        BEGIN
                            -- Get the current count of players joined for this table
                            SELECT COUNT(*)
                            INTO current_player_count
                            FROM joined_players
                            WHERE table_id = NEW.table_id;
                            
                            -- Get the max_players allowed for this table
                            SELECT max_players
                            INTO max_players_allowed
                            FROM table_propositions
                            WHERE id = NEW.table_id;
                            
                            -- Check if adding another player exceeds max_players
                            IF current_player_count + 1 > max_players_allowed THEN
                                RAISE EXCEPTION 'Maximum number of players exceeded for this table';
                            END IF;
                            
                            RETURN NEW;
                        END;
                    $function$
                    ;
                    ''')

        c.execute('''DO $$
                    BEGIN
                        -- Check if the trigger already exists in information_schema.triggers
                        IF NOT EXISTS (
                            SELECT 1
                            FROM information_schema.triggers
                            WHERE trigger_name = 'before_insert_or_update_joined_players'
                        ) THEN
                            -- Create the trigger if it doesn't exist
                            CREATE TRIGGER before_insert_or_update_joined_players
                            BEFORE INSERT OR UPDATE ON joined_players
                            FOR EACH ROW
                            EXECUTE FUNCTION check_max_players();
                        END IF;
                    END $$;
                    ''')

        conn.commit()
        c.close()
        conn.close()

    def get_table_propositions(self, joined_by_me, filter_username):

        if joined_by_me:
            joined_by_me_clause = "and tp.id in (SELECT table_id FROM joined_players jp WHERE LOWER(jp.player_name) = LOWER(%s))"
        else:
            joined_by_me_clause = "and TRUE"
        conn = self.get_db_connection()
        c = conn.cursor()
        c.execute(
            f'''
                SELECT
                    tp.id,
                    tp.game_name,
                    tp.max_players,
                    tp.date, tp.time,
                    tp.duration,
                    tp.notes,
                    tp.bgg_game_id,
                    tp.proposed_by,
                    count(jp.id) as joined_count,
                    array_agg(jp.player_name) 
                FROM 
                    table_propositions tp
                    left join joined_players jp on jp.table_id = tp.id
                WHERE
                    TRUE
                    {joined_by_me_clause}
                    -- check if date is in the future with 1 day of margin
                    and tp.date >= current_date - INTERVAL '1 day'
                group by 
                    tp.id,
                    tp.game_name,
                    tp.max_players,
                    tp.date, tp.time,
                    tp.duration,
                    tp.notes,
                    tp.bgg_game_id,
                    tp.proposed_by
                order by tp.date, tp.time
            ''', (filter_username,)
        )
        propositions = c.fetchall()
        c.close()
        conn.close()

        return propositions

    def create_proposition(self, selected_game, max_players, date_time, time, duration, notes, bgg_game_id, username, join_me_by_default):
        conn = self.get_db_connection()
        c = conn.cursor()
        c.execute('''
                INSERT INTO table_propositions (
                    game_name, 
                    max_players, 
                    date, 
                    time, 
                    duration, 
                    notes, 
                    bgg_game_id, 
                    proposed_by
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
            ''', (
                selected_game,
                max_players,
                date_time.strftime('%Y-%m-%d'),
                time.strftime('%H:%M:%S'),
                duration,
                notes,
                bgg_game_id,
                username
            )
        )

        conn.commit()
        last_row_id = c.fetchone()[0]

        if join_me_by_default:
            self.join_table(last_row_id, username)

        c.close()
        conn.close()

        return last_row_id

    def leave_table(self, table_id, joined_player):
        conn = self.get_db_connection()
        c = conn.cursor()
        c.execute(
            '''DELETE FROM joined_players WHERE table_id = %s AND player_name = %s''',
            (table_id, joined_player)
        )
        conn.commit()
        c.close()
        conn.close()

    def join_table(self, table_id, username):
        conn = self.get_db_connection()
        c = conn.cursor()
        try:
            c.execute(
                '''INSERT INTO joined_players (table_id, player_name) VALUES (%s, %s)''',
                (table_id, username)
            )
            conn.commit()
        except psycopg2.IntegrityError as e:
            print(e)
            raise AttributeError("You have already joined this table.")
        finally:
            c.close()
            conn.close()

    def delete_proposition(self, table_id):
        conn = self.get_db_connection()
        c = conn.cursor()
        c.execute(
            '''DELETE FROM joined_players WHERE table_id = %s''',
            (table_id,)
        )
        c.execute(
            '''DELETE FROM table_propositions WHERE id = %s''',
            (table_id,)
        )
        conn.commit()
        c.close()
        conn.close()

    def update_table_proposition(self, table_id, game_name, max_players, date, time, duration, notes, bgg_game_id):
        conn = self.get_db_connection()
        c = conn.cursor()
        c.execute(
            '''
                UPDATE table_propositions
                SET game_name = %s,
                    max_players = %s,
                    date = %s,
                    time = %s,
                    duration = %s,
                    notes = %s,
                    bgg_game_id = %s
                WHERE id = %s
            ''',
            (game_name, max_players, date, time, duration, notes, bgg_game_id, table_id)
        )
        conn.commit()
        c.close()
        conn.close()