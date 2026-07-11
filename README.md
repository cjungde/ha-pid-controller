# PID Controller (Home Assistant / HACS)

Ein generischer PID-Regler als HACS-Custom-Integration. Anders als PWM-Thermostate (z. B. HASmartThermostat) schreibt dieses Modul einen **vorzeichenbehafteten kontinuierlichen Wert** direkt auf ein Ziel-`number`-Entity – ideal, um z. B. einen Heizkurven-**Setpoint-Shift (–5…+5 K)** zu fahren.

> Entstanden als ausgelagerte PID-Schicht des Projekts [hp-adaptive-control](https://github.com/cjungde/hp-adaptive-control) (adaptive Wärmepumpensteuerung). Die WP-spezifische Logik (Zustandsautomat, Lernfunktion) bleibt dort; hier lebt nur der wiederverwendbare Regler.

---

## Warum nicht HASmartThermostat?

| | HASmartThermostat | Dieses Modul |
|---|---|---|
| Ausgang | PWM auf Switch, oder 0–100 % auf Ventil/Licht | **Signierter Wert** (z. B. –5…+5) auf `number`-Entity |
| „0 = neutral" | nein (0–100 %) | ja – Nullpunkt bleibt erhalten |
| Ziel-Entity | Switch/Licht/Ventil | beliebiges `number`-Entity via `number.set_value` |
| Gaten von außen | umständlich (hvac_mode) | **`switch.enabled`** friert Integral ein, kein Output-Write |
| Rolle | vollwertiges Thermostat | reiner Regler-Baustein |

Für einen **Trim-Ansatz** (interne Heizkurve bleibt Basis, HA korrigiert nur fein) ist der signierte Ausgang der entscheidende Vorteil.

---

## Funktionsprinzip

```
input_entity (Messwert)  ─┐
setpoint (Entity/fest)  ──┼──▶ PID (Kp,Ki,Kd + Ke-Vorsteuerung) ──▶ number.set_value(output_entity)
outdoor_entity (opt.)   ──┘                                          Bereich output_min … output_max
```

- **Derivative on measurement** – kein Derivative-Kick bei Sollwertsprüngen
- **Clamping-Anti-Windup** – Integral wird bei Sättigung eingefroren und auf den Ausgangsbereich begrenzt
- **Ke-Vorsteuerung** – optionale lineare Außentemperatur-Kompensation `Ke · (Sollwert − Außentemp)`
- **`switch.enabled`** – externer Zustandsautomat kann den Regler pausieren; das Integral bleibt eingefroren, es wird nichts geschrieben
- **Warmstart-Persistenz** – Integral, `last_pv` und Enable-Zustand werden im integrationseigenen `Store` gehalten und beim Neustart wiederhergestellt (kein Kaltstart, kein Verlust des eingeregelten Trims). Beim Entfernen des Config-Entries wird der Store automatisch gelöscht.

## Erzeugte Entitäten (je Config-Entry)

| Entity | Zweck |
|--------|-------|
| `sensor.<name>_output` | Aktueller PID-Ausgang; Attribute `pid_p/i/d/e`, `pv`, `setpoint`, `outdoor`, `written` |
| `switch.<name>_enabled` | Regler ein/aus (Integral-Freeze bei aus) |

Der berechnete Wert wird zusätzlich zyklisch auf das konfigurierte `output_entity` geschrieben.

---

## Installation

1. HACS → Integrationen → ⋮ → Benutzerdefinierte Repositories → `https://github.com/cjungde/ha-pid-controller` (Kategorie: Integration)
2. „PID Controller" installieren, Home Assistant neu starten
3. Einstellungen → Geräte & Dienste → Integration hinzufügen → „PID Controller"

## Konfiguration (Config-Flow)

| Feld | Beschreibung |
|------|-------------|
| Input | Messgröße (Sensor/`input_number`), z. B. gemittelte Raumtemperatur oder Bedarfssensor |
| Setpoint-Entity / fester Setpoint | Zielwert; Entity hat Vorrang, sonst fester Wert |
| Output-Entity | `number`-Entity, das geschrieben wird (z. B. `number.…_setpoint_shift_circuit_2`) |
| Outdoor (optional) | Außensensor für Ke-Vorsteuerung |
| Kp / Ki / Kd / Ke | Reglerparameter |
| Output min / max | Ausgangsbereich – **min darf negativ sein** |
| Sample time | Regeltakt in Sekunden (Default 3600 = 1 h; passend für träge FBH) |
| Invert | Kühlrichtung (Fehler-Vorzeichen umkehren) |

Parameter sind nachträglich über **Konfigurieren** (Options-Flow) editierbar, ohne die Integration neu anzulegen.

---

## Anwendungsbeispiel: Wärmepumpen-Shift

```
Input:        sensor.raumtemp_gewichtet   (gemittelter Raum-Istwert)
Setpoint:     input_number.raumsoll        (21 °C)
Output:       number.lg_thermav_r290_setpoint_shift_circuit_2
Output min/max: -5 / +5
Kp/Ki/Kd:     0 / 0.3 / 0     (reines I-Verhalten für träge FBH)
Ke + Outdoor: 0.1 / sensor.wetterstation_temperatur
Sample time:  3600
```

Der Zustandsautomat (in AppDaemon) schaltet `switch.<name>_enabled` bei DHW/Abtauen/Backup/Sommer aus → PID pausiert sauber, das Integral läuft nicht voll.

---

## Entwicklung

Der PID-Kern (`pid.py`) ist HA-unabhängig und testbar:

```bash
python3 tests/test_pid.py
```

## Lizenz

MIT
