// https://docs.cypress.io/api/introduction/api.html

describe('My First Test', () => {
  it('Visits the app root url', () => {
    cy.intercept('GET', '**/settings').as('getSettings');
    cy.visit('/settings');
    cy.wait('@getSettings').then((interception) => {
      cy.log(JSON.stringify(interception.response));
    });
    // cy.visit('/settings', { failOnStatusCode: false });
    // cy.contains('h2', 'The Daily Office');
  });
});
