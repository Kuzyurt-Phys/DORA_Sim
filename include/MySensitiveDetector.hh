// ----------------------------------------------------------------------------
// MySensitiveDetector.hh
// Records energy deposition for the DORA 96-well TLD grid.
// ----------------------------------------------------------------------------
#ifndef MySensitiveDetector_h
#define MySensitiveDetector_h 1

#include "G4VSensitiveDetector.hh"
#include "globals.hh"

class MySensitiveDetector : public G4VSensitiveDetector {
public:
    MySensitiveDetector(G4String name);
    virtual ~MySensitiveDetector();
    virtual G4bool ProcessHits(G4Step* aStep, G4TouchableHistory* ROhist);
};
#endif
