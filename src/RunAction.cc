#include "RunAction.hh"

#include "G4AnalysisManager.hh"
#include "G4Run.hh"
#include "G4RunManager.hh"
#include "G4SystemOfUnits.hh"

RunAction::RunAction()
: G4UserRunAction()
{
    auto analysisManager = G4AnalysisManager::Instance();

    analysisManager->SetVerboseLevel(1);
    analysisManager->SetDefaultFileType("csv");

    analysisManager->CreateNtuple("TLD_Scoring", "Energy Deposition Data");

    analysisManager->CreateNtupleIColumn("TLD_ID");
    analysisManager->CreateNtupleDColumn("Edep_keV");

    // Diagnostic columns
    analysisManager->CreateNtupleIColumn("FromLeadInteraction");
    analysisManager->CreateNtupleIColumn("FromHolderInteraction");
    analysisManager->CreateNtupleIColumn("ParticlePDG");
    analysisManager->CreateNtupleIColumn("ParentID");

    analysisManager->FinishNtuple();
}

RunAction::~RunAction()
{}

void RunAction::BeginOfRunAction(const G4Run*)
{
    G4RunManager::GetRunManager()->SetPrintProgress(500000);

    auto analysisManager = G4AnalysisManager::Instance();
    analysisManager->OpenFile("DORA_Results.csv");
}

void RunAction::EndOfRunAction(const G4Run*)
{
    auto analysisManager = G4AnalysisManager::Instance();

    analysisManager->Write();
    analysisManager->CloseFile();
}
