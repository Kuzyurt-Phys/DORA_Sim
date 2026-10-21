// ----------------------------------------------------------------------------
// DetectorConstruction.cc
// Improved DORA irradiator geometry.
//
// Model features:
//   - cylindrical lead shielding ring, 135 mm radial thickness
//   - rectangular tray channel through the central region
//   - upper and lower lead plugs
//   - source positions at z = +/-120 mm
//   - optional polystyrene holder
//   - unchanged 8x12 LiF TLD array
//   - legacy physical source markers disabled (overlap correction)
//
// Runtime switches:
//   DORA_BUILD_BODY=1              build DORA lead body
//   DORA_BUILD_BODY=0              no lead body
//
//   DORA_BUILD_HOLDER=1            build holder
//   DORA_BUILD_HOLDER=0            no holder, TLDs in air
//
//   DORA_SHOW_SOURCE_MARKERS=1     report disabled legacy markers
//   DORA_SHOW_SOURCE_MARKERS=0     no source markers
//
// Default:
//   body = ON
//   holder = ON
//   source markers = OFF
// ----------------------------------------------------------------------------

#include "DetectorConstruction.hh"
#include "MySensitiveDetector.hh"

#include "G4NistManager.hh"
#include "G4Material.hh"
#include "G4Box.hh"
#include "G4Tubs.hh"
#include "DoraGeometryConfig.hh"
#include "G4SubtractionSolid.hh"
#include "G4LogicalVolume.hh"
#include "G4PVPlacement.hh"
#include "G4SystemOfUnits.hh"
#include "G4VisAttributes.hh"
#include "G4Color.hh"
#include "G4SDManager.hh"
#include "G4ThreeVector.hh"
#include "G4ios.hh"

#include <cstdlib>
#include <string>

DetectorConstruction::DetectorConstruction()
: G4VUserDetectorConstruction(),
  fLogicTLD(nullptr)
{ }

DetectorConstruction::~DetectorConstruction()
{ }

static G4bool EnvSwitchIsOn(const char* value)
{
    if (!value) return false;

    std::string v(value);

    return (
        v == "1" ||
        v == "true" ||
        v == "TRUE" ||
        v == "on" ||
        v == "ON"
    );
}

static G4bool EnvSwitchIsOff(const char* value)
{
    if (!value) return false;

    std::string v(value);

    return (
        v == "0" ||
        v == "false" ||
        v == "FALSE" ||
        v == "off" ||
        v == "OFF"
    );
}

G4VPhysicalVolume* DetectorConstruction::Construct()
{
    G4NistManager* nist = G4NistManager::Instance();

    // ------------------------------------------------------------------------
    // 1. Materials
    // ------------------------------------------------------------------------
    G4Material* world_mat  = nist->FindOrBuildMaterial("G4_AIR");
    G4Material* holder_mat = nist->FindOrBuildMaterial("G4_POLYSTYRENE");
    G4Material* tld_mat    = nist->FindOrBuildMaterial("G4_LITHIUM_FLUORIDE");
    G4Material* lead_mat   = nist->FindOrBuildMaterial("G4_Pb");


    G4bool buildDoraBody = true;
    G4bool buildHolder   = true;
    G4bool showSourceMarkers = false;

    if (EnvSwitchIsOff(std::getenv("DORA_BUILD_BODY"))) {
        buildDoraBody = false;
    }

    if (EnvSwitchIsOff(std::getenv("DORA_BUILD_HOLDER"))) {
        buildHolder = false;
    }

    if (EnvSwitchIsOn(std::getenv("DORA_SHOW_SOURCE_MARKERS"))) {
        showSourceMarkers = true;
    }

    G4cout << "\n[DORA geometry settings]" << G4endl;
    G4cout << "  Build DORA lead body:       " << (buildDoraBody ? "YES" : "NO") << G4endl;
    G4cout << "  Build holder:               " << (buildHolder ? "YES" : "NO") << G4endl;
    G4cout << "  Show source markers:        " << (showSourceMarkers ? "YES" : "NO") << G4endl;
    G4cout << "  Lead shielding material:    G4_Pb" << G4endl;
    G4cout << "  Plug inner |z| (assumed):    " << DoraConfig::PlugInnerZmm() << " mm" << G4endl;
    G4cout << "  Holder model: solid polystyrene box; actual carriage/plate not yet established" << G4endl;
    G4cout << "  Channel width 100 mm: modelling assumption, not measured" << G4endl;
    G4cout << "  Geometry version:           lead ring with rectangular tray channel" << G4endl;
    G4cout << G4endl;

    // ------------------------------------------------------------------------
    // 2. World volume
    // ------------------------------------------------------------------------
    G4double world_size = 0.80 * m;

    G4Box* solidWorld =
        new G4Box("World", world_size, world_size, world_size);

    G4LogicalVolume* logicWorld =
        new G4LogicalVolume(solidWorld, world_mat, "World");

    G4VPhysicalVolume* physWorld =
        new G4PVPlacement(
            nullptr,
            G4ThreeVector(),
            logicWorld,
            "World",
            nullptr,
            false,
            0,
            true
        );

    logicWorld->SetVisAttributes(G4VisAttributes::GetInvisible());

    // ------------------------------------------------------------------------
    // 3. DORA lead shielding
    //
    // Document-guided dimensions:
    //   total outer diameter/width: about 360 mm
    //   lead ring thickness:        135 mm
    //   central cavity diameter:     90 mm
    //   source distance:             +/-120 mm
    //   total height:                600 mm
    //
    // Improved model:
    //   lateral shielding is a cylindrical ring:
    //       inner radius = 45 mm
    //       outer radius = 180 mm
    //       height       = 600 mm
    //
    //   a rectangular tray channel is subtracted through the middle:
    //       along x: fully through the body
    //       y opening: slightly larger than the holder width
    //       z opening: 30 mm, matching the schematic central slot
    //
    //   lead plugs:
    //       radius = 45 mm
    //       default z = +120 ... +300 mm (unverified plug depth)
    //       default z = -300 ... -120 mm (unverified plug depth)
    //
    // This keeps the real idea of a tray passage, without making the whole
    // central slice artificially open in all directions.
    // ------------------------------------------------------------------------
    if (buildDoraBody) {

        G4double outerRadius = 180.0 * mm;
        G4double cavityRadius = 45.0 * mm;
        G4double totalHeight = 600.0 * mm;

        G4double zOuter = 300.0 * mm;
        G4double plugInnerZ = DoraConfig::PlugInnerZmm() * mm;

        // Tray channel dimensions.
        //
        // Holder is 127.55 x 85.3 x 19.0 mm.
        // The DORA document gives sample region around 129 x 73 mm and max height 17 mm.
        // We use a slightly larger channel than the holder to avoid artificial overlap.
        G4double trayChannelHalfX = 220.0 * mm;  // cut fully through lead body
        G4double trayChannelHalfY = 50.0  * mm;  // covers holder width
        G4double trayChannelHalfZ = 15.0  * mm;  // 30 mm central slot

        // Lateral lead ring before tray cut.
        G4Tubs* solidLeadRingRaw =
            new G4Tubs(
                "DORA_LeadRing_Raw_Solid",
                cavityRadius,
                outerRadius,
                0.5 * totalHeight,
                0.0,
                360.0 * deg
            );

        // Rectangular tray channel to subtract.
        G4Box* solidTrayChannel =
            new G4Box(
                "DORA_TrayChannel_Cut_Solid",
                trayChannelHalfX,
                trayChannelHalfY,
                trayChannelHalfZ
            );

        G4SubtractionSolid* solidLeadRingWithTray =
            new G4SubtractionSolid(
                "DORA_LeadRingWithTrayChannel_Solid",
                solidLeadRingRaw,
                solidTrayChannel,
                nullptr,
                G4ThreeVector(0.0, 0.0, 0.0)
            );

        G4LogicalVolume* logicLeadRing =
            new G4LogicalVolume(
                solidLeadRingWithTray,
                lead_mat,
                "DORA_LeadRingWithTrayChannel_Log"
            );

        G4VisAttributes* leadRingVis =
            new G4VisAttributes(G4Color(0.55, 0.55, 0.55, 0.25));
        leadRingVis->SetForceWireframe(true);
        logicLeadRing->SetVisAttributes(leadRingVis);

        new G4PVPlacement(
            nullptr,
            G4ThreeVector(0.0, 0.0, 0.0),
            logicLeadRing,
            "DORA_LeadRingWithTrayChannel_Phys",
            logicWorld,
            false,
            1001,
            true
        );

        // Upper/lower lead plugs.
        G4double plugLength = zOuter - plugInnerZ;
        G4double upperPlugCenterZ = plugInnerZ + 0.5 * plugLength;
        G4double lowerPlugCenterZ = -upperPlugCenterZ;

        G4Tubs* solidLeadPlug =
            new G4Tubs(
                "DORA_LeadPlug_Solid",
                0.0,
                cavityRadius,
                0.5 * plugLength,
                0.0,
                360.0 * deg
            );

        G4LogicalVolume* logicLeadPlug =
            new G4LogicalVolume(
                solidLeadPlug,
                lead_mat,
                "DORA_LeadPlug_Log"
            );

        G4VisAttributes* leadPlugVis =
            new G4VisAttributes(G4Color(0.25, 0.25, 0.25, 0.35));
        leadPlugVis->SetForceWireframe(true);
        logicLeadPlug->SetVisAttributes(leadPlugVis);

        new G4PVPlacement(
            nullptr,
            G4ThreeVector(0.0, 0.0, upperPlugCenterZ),
            logicLeadPlug,
            "DORA_UpperLeadPlug_Phys",
            logicWorld,
            false,
            2001,
            true
        );

        new G4PVPlacement(
            nullptr,
            G4ThreeVector(0.0, 0.0, lowerPlugCenterZ),
            logicLeadPlug,
            "DORA_LowerLeadPlug_Phys",
            logicWorld,
            false,
            2002,
            true
        );
    }

    // ------------------------------------------------------------------------
    // 4. Optional source markers for visualization only
    //
    // The real radioactive source is still generated by PrimaryGeneratorAction.
    // Legacy physical spheres are disabled because they intersected the lead plugs.
    // Keep DORA_SHOW_SOURCE_MARKERS=0 for production dose runs.
    // ------------------------------------------------------------------------
    if (showSourceMarkers) {
        G4cout << "WARNING: physical source markers are disabled: the legacy spheres overlap lead. "
               << "No marker volumes have been placed." << G4endl;
    }

    // ------------------------------------------------------------------------
    // 5. Holder and TLD geometry
    // ------------------------------------------------------------------------
    G4double holderX = 127.55 * mm;
    G4double holderY = 85.3 * mm;
    G4double holderZ = 19.0 * mm;

    const G4double holderOffsetX = DoraConfig::HolderXmm() * mm;

    G4cout << "  Holder/TLD displacement along x: "
           << holderOffsetX / mm << " mm" << G4endl;
    G4LogicalVolume* logicHolder = nullptr;
    G4LogicalVolume* tldMotherVolume = logicWorld;

    if (buildHolder) {
        G4Box* solidHolder =
            new G4Box("Holder", 0.5*holderX, 0.5*holderY, 0.5*holderZ);

        logicHolder =
            new G4LogicalVolume(solidHolder, holder_mat, "Holder");

        new G4PVPlacement(
            nullptr,
            G4ThreeVector(holderOffsetX, 0.0, 0.0),
            logicHolder,
            "Holder",
            logicWorld,
            false,
            0,
            true
        );

        G4VisAttributes* holderVis =
            new G4VisAttributes(G4Color(1.0, 1.0, 1.0, 0.20));
        holderVis->SetForceWireframe(true);
        logicHolder->SetVisAttributes(holderVis);

        tldMotherVolume = logicHolder;
    }

    // TLD array.
    G4double tld_diam  = 7.0 * mm;
    G4double tld_thick = 1.0 * mm;
    G4double pitch     = 9.0 * mm;

    G4double startX = -0.5 * holderX + 14.275 * mm;
    G4double startY =  0.5 * holderY - 11.15  * mm;

    G4Tubs* solidTLD =
        new G4Tubs(
            "TLD",
            0.0,
            0.5*tld_diam,
            0.5*tld_thick,
            0.0,
            360.0*deg
        );

    fLogicTLD =
        new G4LogicalVolume(solidTLD, tld_mat, "TLD_Log");

    G4VisAttributes* tldVis =
        new G4VisAttributes(G4Color(0.0, 0.0, 1.0, 1.0));
    tldVis->SetForceSolid(true);
    fLogicTLD->SetVisAttributes(tldVis);

    for (G4int row = 0; row < 8; row++) {
        for (G4int col = 0; col < 12; col++) {

            G4double xPos = startX + col * pitch;
            G4double yPos = startY - row * pitch;

            G4int copyNo = row * 12 + col;

            auto* tldPlacement = new G4PVPlacement(
                nullptr,
                G4ThreeVector(
                    xPos + (buildHolder ? 0.0 : holderOffsetX),
                    yPos,
                    0.0
                ),
                fLogicTLD,
                "TLD_Phys",
                tldMotherVolume,
                false,
                copyNo,
                true
            );
        if (copyNo == 0) {
            const G4ThreeVector localPosition =
                tldPlacement->GetTranslation();

            G4cout << "  TLD 0 mother: "
                   << tldMotherVolume->GetName()
                   << "; local position (mm): "
                   << localPosition / mm
                   << G4endl;
        }
        }
    }

    G4cout << "  TLD material: " << tld_mat->GetName()
           << "; density: " << tld_mat->GetDensity()/(g/cm3)
           << " g/cm3; individual mass: " << fLogicTLD->GetMass()/g << " g" << G4endl;
    return physWorld;
}

void DetectorConstruction::ConstructSDandField()
{
    G4SDManager* sdManager = G4SDManager::GetSDMpointer();

    MySensitiveDetector* sensitiveTLD =
        new MySensitiveDetector("TLD_SD");

    sdManager->AddNewDetector(sensitiveTLD);

    SetSensitiveDetector(fLogicTLD, sensitiveTLD);
}
