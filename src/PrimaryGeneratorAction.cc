// ----------------------------------------------------------------------------
// PrimaryGeneratorAction.cc
// Two fixed Cs-137 gamma sources with isotropic 4pi emission.
//
// Default source distance:
//   z = +/-120 mm
//
// Optional test override:
//   DORA_SOURCE_Z_MM=120 ./DORA_Sim run.mac
// ----------------------------------------------------------------------------

#include "PrimaryGeneratorAction.hh"
#include "DoraGeometryConfig.hh"

#include "G4ParticleGun.hh"
#include "G4ParticleTable.hh"
#include "G4ParticleDefinition.hh"
#include "G4SystemOfUnits.hh"
#include "G4PhysicalConstants.hh"
#include "G4ThreeVector.hh"
#include "G4ios.hh"
#include "Randomize.hh"

#include <cstdlib>
#include <cmath>

PrimaryGeneratorAction::PrimaryGeneratorAction()
: G4VUserPrimaryGeneratorAction(),
  fParticleGun(nullptr),
  fSourceZ(120.0 * mm)
{
    G4int n_particle = 1;
    fParticleGun = new G4ParticleGun(n_particle);

    G4ParticleTable* particleTable = G4ParticleTable::GetParticleTable();
    G4ParticleDefinition* particle = particleTable->FindParticle("gamma");

    fParticleGun->SetParticleDefinition(particle);
    fParticleGun->SetParticleEnergy(661.7 * keV);

    fSourceZ = DoraConfig::SourceZmm() * mm;
    const char* body = std::getenv("DORA_BUILD_BODY");
    const std::string bodySetting = body ? body : "1";
    const bool hasBody = !(bodySetting == "0" || bodySetting == "false" || bodySetting == "FALSE" || bodySetting == "off" || bodySetting == "OFF");
    if (hasBody && fSourceZ/mm >= DoraConfig::PlugInnerZmm() && fSourceZ/mm <= 300.0) {
        G4cout << "WARNING: point source is on or inside the assumed lead plug. "
               << "This legacy geometry is not validated for quantitative dose prediction. "
               << "Obtain plug/capsule dimensions before production interpretation." << G4endl;
    }

    G4cout << "\n[DORA source settings]" << G4endl;
    G4cout << "  Particle: gamma" << G4endl;
    G4cout << "  Energy:   661.7 keV" << G4endl;
    G4cout << "  Sources:  z = +/- " << fSourceZ / mm << " mm" << G4endl;
    G4cout << "  Emission: isotropic 4pi" << G4endl;
    G4cout << G4endl;
}

PrimaryGeneratorAction::~PrimaryGeneratorAction()
{
    delete fParticleGun;
}

void PrimaryGeneratorAction::GeneratePrimaries(G4Event* anEvent)
{
    // Randomly choose upper or lower source with equal probability.
    if (G4UniformRand() < 0.5) {
        fParticleGun->SetParticlePosition(G4ThreeVector(0.0, 0.0, +fSourceZ));
    } else {
        fParticleGun->SetParticlePosition(G4ThreeVector(0.0, 0.0, -fSourceZ));
    }

    // Isotropic direction over 4pi.
    G4double cosTheta = 2.0 * G4UniformRand() - 1.0;
    G4double sinTheta = std::sqrt(1.0 - cosTheta*cosTheta);
    G4double phi = 2.0 * pi * G4UniformRand();

    G4double vx = sinTheta * std::cos(phi);
    G4double vy = sinTheta * std::sin(phi);
    G4double vz = cosTheta;

    fParticleGun->SetParticleMomentumDirection(G4ThreeVector(vx, vy, vz));

    fParticleGun->GeneratePrimaryVertex(anEvent);
}
