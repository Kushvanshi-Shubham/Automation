param(
    [Parameter(Mandatory = $true)][string]$Email,
    [int]$Amount = 10
)

$env:PGPASSWORD = "postgres"
$psql = "C:\Program Files\PostgreSQL\16\bin\psql.exe"

$sql = @"
DO `$`$
DECLARE uid uuid;
BEGIN
  SELECT id INTO uid FROM users WHERE email = '$Email';
  IF uid IS NULL THEN RAISE EXCEPTION 'No user with email %', '$Email'; END IF;
  UPDATE users SET credit_balance = credit_balance + $Amount WHERE id = uid;
  INSERT INTO credit_ledger (id, user_id, amount, type, description, created_at)
  VALUES (gen_random_uuid(), uid, $Amount, 'admin_adjustment', 'Manual grant via script', now());
END
`$`$;
"@

& $psql -U postgres -h localhost -d kliptos -c $sql
& $psql -U postgres -h localhost -d kliptos -c "SELECT email, credit_balance FROM users WHERE email = '$Email';"
