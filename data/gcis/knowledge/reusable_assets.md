# Reusable Asset Inventory

Update when a component is reused ≥2 times or promoted to standard.

| Asset | Path / ID | Type | Reuse | Notes |
|---|---|---|---|---|
| Generational Method doctrine | `GENERATIONAL_METHOD.md` | Teaching | High | Locked |
| Teaching choreography | `services/animation/teaching_choreography.py` | Animation | High | Beat plans per demo_id |
| Lip-sync performer | `services/animation/performer.py` | Animation | High | educator_mode |
| Stick figure + gestures | `services/animation/stick_figure.py` | Character | High | CHAR-STICK-001 |
| Educator demos (physics) | `services/animation/educator_demos.py` | Demo | Med | bowling, gravity |
| Biology demos | `services/animation/biology_demos.py` | Demo | High | 5 Vol1 demos |
| Physics demos | `services/animation/physics_demos.py` | Demo | Med | Vol1 overlays |
| Biology Academy runner | `scripts/biology_academy_vol1.py` | Production | High | Template for series |
| Educator benchmarks runner | `scripts/educator_benchmarks.py` | Production | Med | Method validation |
| Physics Academy runner | `scripts/physics_academy_vol1.py` | Production | Med | Series pattern |
| unique_path export helper | series scripts | Ops | High | Never overwrite |
| Animation Studio library | `data/animation_studio/library/` | Presets | Med | Camera presets |
| Character CHAR-STICK-001 | `data/universe/characters/CHAR-STICK-001/` | IP | High | Educator host |
| Series: Biology Academy | `data/universe/series/biology_academy/` | Series | High | Vol1 bible |
| Series: Physics Academy | `data/universe/series/physics_academy/` | Series | Med | Vol1 bible |
| Content knowledge store | `services/knowledge.py` + `data/knowledge/` | SEO/hooks | Med | Analytics feed |

## Promotion backlog
- [ ] Demo library registry with version + reuse_count  
- [ ] Shared lab backdrop / palette module (biology PAL → shared)  
- [ ] SEO pack template for Academy episodes  
- [ ] PhonemeMouthDriver (upgrade from amplitude)  
