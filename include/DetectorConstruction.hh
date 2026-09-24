// ----------------------------------------------------------------------------
// DetectorConstruction.hh
// ----------------------------------------------------------------------------
#ifndef DetectorConstruction_h
#define DetectorConstruction_h 1

#include "G4VUserDetectorConstruction.hh"
#include "globals.hh"

class G4VPhysicalVolume;
class G4LogicalVolume;

class DetectorConstruction : public G4VUserDetectorConstruction
{
  public:
    DetectorConstruction();
    virtual ~DetectorConstruction();

    virtual G4VPhysicalVolume* Construct() override;
    virtual void ConstructSDandField() override;

  private:
    G4LogicalVolume* fLogicTLD; // Pointer to the TLD volume for scoring
};

#endif
